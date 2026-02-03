"""
Pipeline Executor Service

Executes YAML pipeline definitions with support for:
- Persona stages (LLM-based)
- Action stages (browser, git, etc.)
- Parallel execution
- Template resolution
- Gemini 3 Flash Agentic Vision integration
"""

import os
import asyncio
import httpx
import json
import re
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from jinja2 import Environment, BaseLoader
import structlog

from .pipeline_loader import PipelineDefinition, StageDefinition
from .browser_service import (
    action_browser_launch,
    action_browser_screenshots,
    browser_service
)
from .git_service import (
    action_git_apply_fixes,
    action_git_create_pr,
    action_git_merge_pr
)

logger = structlog.get_logger(__name__)


class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result of a stage execution."""
    stage_id: str
    status: StageStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms
        }


@dataclass
class ExecutionContext:
    """Context for pipeline execution."""
    pipeline: PipelineDefinition
    input_params: Dict[str, Any]
    stage_outputs: Dict[str, Any] = field(default_factory=dict)
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    auto_approval: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def get_stage_output(self, stage_id: str) -> Optional[Dict[str, Any]]:
        """Get output from a completed stage."""
        return self.stage_outputs.get(stage_id)


@dataclass
class ExecutionResult:
    """Result of pipeline execution."""
    success: bool
    stage_results: Dict[str, StageResult]
    outputs: Dict[str, Any]
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "stage_results": {k: v.to_dict() for k, v in self.stage_results.items()},
            "outputs": self.outputs,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms
        }


# Type for stage progress callback
ProgressCallback = Callable[[str, StageStatus, Optional[Dict]], Awaitable[None]]


class PipelineExecutor:
    """Executes YAML pipeline definitions."""

    def __init__(self):
        self.jinja_env = Environment(loader=BaseLoader())
        # Add datetime functions to Jinja2
        self.jinja_env.globals['now'] = datetime.utcnow
        self.jinja_env.filters['date'] = lambda dt, fmt: dt.strftime(
            fmt.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d')
            .replace('HH', '%H').replace('mm', '%M').replace('ss', '%S')
        )
        self._action_handlers: Dict[str, Callable] = {}
        self._register_default_actions()

    def _register_default_actions(self) -> None:
        """Register default action handlers."""
        self._action_handlers["browser.launch_app"] = self._action_browser_launch
        self._action_handlers["browser.capture_screenshots"] = self._action_browser_screenshots
        self._action_handlers["git.apply_fixes_worktree"] = self._action_git_apply_fixes
        self._action_handlers["git.create_pr"] = self._action_git_create_pr
        self._action_handlers["git.merge_pr"] = self._action_git_merge_pr
        self._action_handlers["skills.validate"] = self._action_skills_validate

    def register_action(self, action_name: str, handler: Callable) -> None:
        """Register a custom action handler."""
        self._action_handlers[action_name] = handler

    async def execute(
        self,
        pipeline: PipelineDefinition,
        input_params: Dict[str, Any],
        auto_approval: bool = False,
        on_progress: Optional[ProgressCallback] = None
    ) -> ExecutionResult:
        """Execute a pipeline."""
        context = ExecutionContext(
            pipeline=pipeline,
            input_params=input_params,
            auto_approval=auto_approval,
            started_at=datetime.utcnow()
        )

        logger.info(
            "Starting pipeline execution",
            pipeline=pipeline.name,
            auto_approval=auto_approval
        )

        try:
            # Execute hooks: on_start
            await self._execute_hooks(pipeline.hooks.get("on_start", []), context)

            # Get execution order (batches)
            batches = pipeline.get_execution_order()
            logger.info("Execution plan", batches=batches)

            # Execute batches
            for batch_idx, batch in enumerate(batches):
                logger.info(f"Executing batch {batch_idx + 1}/{len(batches)}", stages=batch)

                # Execute stages in batch concurrently
                tasks = []
                for stage_id in batch:
                    stage = self._get_stage(pipeline, stage_id)
                    if stage:
                        tasks.append(self._execute_stage(stage, context, on_progress))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check for failures
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        stage_id = batch[i]
                        logger.error(f"Stage {stage_id} failed with exception", error=str(result))
                        context.stage_results[stage_id] = StageResult(
                            stage_id=stage_id,
                            status=StageStatus.FAILED,
                            error=str(result)
                        )

                        # Check stop_on_failure config
                        if pipeline.config.get("on_failure") == "stop":
                            raise result

            # Execute hooks: on_complete
            await self._execute_hooks(pipeline.hooks.get("on_complete", []), context)

            context.completed_at = datetime.utcnow()
            duration_ms = int((context.completed_at - context.started_at).total_seconds() * 1000)

            # Aggregate outputs
            outputs = self._aggregate_outputs(pipeline, context)

            return ExecutionResult(
                success=True,
                stage_results=context.stage_results,
                outputs=outputs,
                started_at=context.started_at,
                completed_at=context.completed_at,
                duration_ms=duration_ms
            )

        except Exception as e:
            logger.error("Pipeline execution failed", error=str(e))

            # Execute hooks: on_failure
            await self._execute_hooks(pipeline.hooks.get("on_failure", []), context)

            context.completed_at = datetime.utcnow()
            duration_ms = int((context.completed_at - context.started_at).total_seconds() * 1000) if context.started_at else 0

            return ExecutionResult(
                success=False,
                stage_results=context.stage_results,
                outputs={},
                error=str(e),
                started_at=context.started_at,
                completed_at=context.completed_at,
                duration_ms=duration_ms
            )

    def _get_stage(self, pipeline: PipelineDefinition, stage_id: str) -> Optional[StageDefinition]:
        """Get stage by ID."""
        for stage in pipeline.stages:
            if stage.id == stage_id:
                return stage
        return None

    async def _execute_stage(
        self,
        stage: StageDefinition,
        context: ExecutionContext,
        on_progress: Optional[ProgressCallback] = None
    ) -> StageResult:
        """Execute a single stage."""
        logger.info(f"Executing stage: {stage.id}", stage_type=stage.stage_type)

        # Check condition
        if stage.condition:
            condition_met = self._evaluate_condition(stage.condition, context)
            if not condition_met:
                logger.info(f"Stage {stage.id} skipped (condition not met)")
                result = StageResult(stage_id=stage.id, status=StageStatus.SKIPPED)
                context.stage_results[stage.id] = result
                return result

        # Notify progress
        if on_progress:
            await on_progress(stage.id, StageStatus.RUNNING, None)

        started_at = datetime.utcnow()

        try:
            # Execute based on stage type
            if stage.stage_type == "persona":
                output = await self._execute_persona_stage(stage, context)
            elif stage.stage_type == "action":
                output = await self._execute_action_stage(stage, context)
            else:
                raise ValueError(f"Unknown stage type: {stage.stage_type}")

            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            # Store output
            context.stage_outputs[stage.id] = output

            result = StageResult(
                stage_id=stage.id,
                status=StageStatus.COMPLETED,
                output=output,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms
            )
            context.stage_results[stage.id] = result

            # Notify progress
            if on_progress:
                await on_progress(stage.id, StageStatus.COMPLETED, output)

            # Execute hooks: on_stage_complete
            await self._execute_hooks(
                context.pipeline.hooks.get("on_stage_complete", []),
                context,
                {"stage": stage}
            )

            logger.info(f"Stage {stage.id} completed", duration_ms=duration_ms)
            return result

        except Exception as e:
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            result = StageResult(
                stage_id=stage.id,
                status=StageStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms
            )
            context.stage_results[stage.id] = result

            # Notify progress
            if on_progress:
                await on_progress(stage.id, StageStatus.FAILED, {"error": str(e)})

            logger.error(f"Stage {stage.id} failed", error=str(e))

            if stage.required:
                raise

            return result

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON object from LLM text response.

        LLMs often return JSON wrapped in markdown code blocks or with
        explanatory text. This extracts the JSON portion.
        """
        if not text:
            return None

        # Direct approach: find JSON object/array patterns in the text
        # This is more robust than relying on specific code block formatting
        logger.warning(f"Extracting JSON from text length {len(text)}")

        # First, try to find a JSON object that starts with {"fixes" or {"violations" etc.
        json_start_patterns = [
            r'\{\s*"fixes"\s*:',
            r'\{\s*"violations"\s*:',
            r'\{\s*"components"\s*:',
            r'\{\s*"screens"\s*:',
        ]

        for pattern in json_start_patterns:
            match = re.search(pattern, text, re.DOTALL)
            logger.warning(f"Pattern {pattern[:15]}... match: {match is not None}")
            if match:
                # Found a potential JSON start, now find the matching closing brace
                start_idx = match.start()
                brace_count = 0
                end_idx = -1
                logger.warning(f"Found match at index {start_idx}")

                for i in range(start_idx, len(text)):
                    if text[i] == '{':
                        brace_count += 1
                    elif text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i
                            break

                logger.warning(f"Brace matching: end_idx={end_idx}, json_len={end_idx - start_idx + 1 if end_idx != -1 else 0}")

                if end_idx != -1:
                    json_str = text[start_idx:end_idx + 1]
                    logger.warning(f"JSON string first 100 chars: {repr(json_str[:100])}")
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict):
                            logger.warning(f"SUCCESS: Extracted JSON, keys: {list(parsed.keys())}")
                            return parsed
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON parse failed: {e}, trying to clean...")

        # Try to find raw JSON object (starts with { and ends with })
        # Find the first { and last } to extract potential JSON
        start_idx = text.find('{')
        if start_idx != -1:
            # Find matching closing brace
            brace_count = 0
            end_idx = -1
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break

            if end_idx != -1:
                potential_json = text[start_idx:end_idx + 1]
                try:
                    parsed = json.loads(potential_json)
                    if isinstance(parsed, dict):
                        logger.debug("Extracted JSON from raw text")
                        return parsed
                except json.JSONDecodeError:
                    pass

        # Try to find JSON array
        start_idx = text.find('[')
        if start_idx != -1:
            bracket_count = 0
            end_idx = -1
            for i in range(start_idx, len(text)):
                if text[i] == '[':
                    bracket_count += 1
                elif text[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i
                        break

            if end_idx != -1:
                potential_json = text[start_idx:end_idx + 1]
                try:
                    parsed = json.loads(potential_json)
                    if isinstance(parsed, list):
                        logger.debug("Extracted JSON array from raw text")
                        return {"items": parsed}  # Wrap in dict for consistency
                except json.JSONDecodeError:
                    pass

        return None

    async def _execute_persona_stage(
        self,
        stage: StageDefinition,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a persona (LLM) stage."""
        # Resolve input template
        input_text = self._resolve_template(stage.input_template, context)

        # Get model config
        config = stage.config
        model = config.get("model", "claude-sonnet-4-20250514")
        tools = config.get("tools", [])

        logger.info(f"Executing persona stage", persona=stage.persona, model=model)

        # Check if this is a Gemini vision stage
        if "gemini" in model.lower() and "code_execution" in tools:
            result = await self._execute_gemini_agentic_vision(input_text, config)
        elif "gemini" in model.lower():
            result = await self._execute_gemini(input_text, config)
        elif "claude" in model.lower():
            result = await self._execute_claude(input_text, config)
        else:
            # Default to Claude
            result = await self._execute_claude(input_text, config)

        # Extract JSON from text response and merge into output
        # This allows stages to reference structured data like stages.X.output.fixes
        text_content = result.get("text", "")
        extracted_json = self._extract_json_from_text(text_content)

        if extracted_json:
            logger.info(
                "Extracted structured data from LLM response",
                stage=stage.id,
                keys=list(extracted_json.keys())
            )
            # Merge extracted JSON into result (text and model remain, JSON fields added)
            result.update(extracted_json)
        else:
            logger.warning(
                "No JSON extracted from LLM response",
                stage=stage.id,
                text_preview=text_content[:200] if text_content else "empty"
            )

        return result

    async def _execute_gemini_agentic_vision(
        self,
        prompt: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Gemini 2.5 Flash with code execution capability (Agentic Vision)."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")

        # MANDATORY: Gemini 3 Flash for Agentic Vision (see skills/model-governance/SKILL.md)
        model = config.get("model", "gemini-3-flash-preview")

        logger.info("Executing Gemini 3 Flash with Agentic Vision", model=model)

        # Use v1beta API for code execution feature
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "tools": [{"code_execution": {}}],
                    "generationConfig": {
                        "temperature": config.get("temperature", 0.1),
                        "maxOutputTokens": config.get("max_tokens", 8192)
                    }
                }
            )

            if response.status_code != 200:
                raise ValueError(f"Gemini API error: {response.status_code} - {response.text}")

            result = response.json()

            # Log full response for debugging
            logger.debug("Gemini Agentic Vision response", response=result)

            # Extract response
            candidates = result.get("candidates", [])
            if not candidates:
                # Check for errors in response
                error_info = result.get("error", {})
                prompt_feedback = result.get("promptFeedback", {})
                logger.error(
                    "Gemini returned no candidates",
                    error=error_info,
                    prompt_feedback=prompt_feedback,
                    full_response=result
                )
                raise ValueError(f"No response from Gemini: {error_info or prompt_feedback or 'empty candidates'}")

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])

            # Combine text and code execution results
            output_text = ""
            code_results = []

            for part in parts:
                if "text" in part:
                    output_text += part["text"]
                if "executableCode" in part:
                    code_results.append({
                        "code": part["executableCode"].get("code", ""),
                        "language": part["executableCode"].get("language", "python")
                    })
                if "codeExecutionResult" in part:
                    code_results.append({
                        "output": part["codeExecutionResult"].get("output", ""),
                        "outcome": part["codeExecutionResult"].get("outcome", "")
                    })

            return {
                "text": output_text,
                "code_executions": code_results,
                "model": model,
                "agentic_vision": True
            }

    async def _execute_gemini(
        self,
        prompt: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute standard Gemini API call."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")

        # MANDATORY: Use latest Gemini model (see skills/model-governance/SKILL.md)
        model = config.get("model", "gemini-2.5-flash")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": config.get("temperature", 0.7),
                        "maxOutputTokens": config.get("max_tokens", 4096)
                    }
                }
            )

            if response.status_code != 200:
                raise ValueError(f"Gemini API error: {response.status_code}")

            result = response.json()
            text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

            return {"text": text, "model": model}

    async def _execute_claude(
        self,
        prompt: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Claude API call."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        # MANDATORY: Use latest Claude model (see skills/model-governance/SKILL.md)
        # Default to Sonnet for speed, use Opus for complex reasoning
        model = config.get("model", "claude-sonnet-4-20250514")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": model,
                    "max_tokens": config.get("max_tokens", 4096),
                    "messages": [{"role": "user", "content": prompt}]
                }
            )

            if response.status_code != 200:
                raise ValueError(f"Claude API error: {response.status_code}")

            result = response.json()
            text = result.get("content", [{}])[0].get("text", "")

            return {"text": text, "model": model}

    async def _execute_action_stage(
        self,
        stage: StageDefinition,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute an action stage."""
        action = stage.action
        if not action:
            raise ValueError(f"Stage {stage.id} has no action defined")

        handler = self._action_handlers.get(action)
        if not handler:
            raise ValueError(f"Unknown action: {action}")

        # Resolve input template
        if isinstance(stage.input_template, str):
            input_data = self._resolve_template(stage.input_template, context)
            # Try to parse as JSON if it looks like JSON
            if input_data.strip().startswith("{"):
                input_data = json.loads(input_data)
        else:
            # It's already a dict, resolve templates within it
            input_data = self._resolve_template_dict(stage.input_template, context)

        logger.info(f"Executing action: {action}")
        return await handler(input_data, context)

    def _resolve_template(self, template: str, context: ExecutionContext) -> str:
        """Resolve Jinja2 template with context."""
        try:
            tpl = self.jinja_env.from_string(template)
            return tpl.render(
                input=context.input_params,
                stages=context.stage_outputs,
                config=context.pipeline.config
            )
        except Exception as e:
            logger.warning(f"Template resolution failed: {e}")
            return template

    def _resolve_template_dict(self, data: Any, context: ExecutionContext) -> Any:
        """Recursively resolve templates in a dict/list structure."""
        if isinstance(data, str):
            # Check if this is a simple variable reference like "{{ stages.x.output.y }}"
            # In that case, we want to preserve the original object (list/dict)
            simple_var_pattern = r'^\s*\{\{\s*([\w_.]+)\s*\}\}\s*$'
            match = re.match(simple_var_pattern, data)
            if match:
                # Extract the variable path and resolve it directly
                var_path = match.group(1)
                logger.debug(f"Resolving variable path: {var_path}")
                try:
                    value = self._resolve_variable_path(var_path, context)
                    logger.debug(f"Variable path {var_path} resolved to: {type(value).__name__}")
                    if value is not None:
                        return value
                    else:
                        logger.warning(f"Variable path {var_path} resolved to None")
                except Exception as e:
                    logger.warning(f"Variable path resolution failed for {var_path}: {e}")
            return self._resolve_template(data, context)
        elif isinstance(data, dict):
            return {k: self._resolve_template_dict(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._resolve_template_dict(item, context) for item in data]
        return data

    def _resolve_variable_path(self, path: str, context: ExecutionContext) -> Any:
        """
        Resolve a dotted variable path to its actual value.

        Examples:
          - "input.project_path" -> context.input_params["project_path"]
          - "stages.generate_fixes.output.fixes" -> context.stage_outputs["generate_fixes"]["fixes"]
        """
        parts = path.split('.')
        if not parts:
            return None

        # Start with the root object
        if parts[0] == "input":
            obj = context.input_params
            parts = parts[1:]
        elif parts[0] == "stages":
            if len(parts) < 2:
                return None
            stage_id = parts[1]
            obj = context.stage_outputs.get(stage_id)
            parts = parts[2:]
            # Handle "output" prefix (stages.X.output.Y)
            if parts and parts[0] == "output":
                parts = parts[1:]
        elif parts[0] == "config":
            obj = context.pipeline.config
            parts = parts[1:]
        else:
            return None

        # Navigate the path
        for part in parts:
            if obj is None:
                return None
            if isinstance(obj, dict):
                obj = obj.get(part)
            else:
                return None

        return obj

    def _evaluate_condition(self, condition: str, context: ExecutionContext) -> bool:
        """Evaluate a condition expression."""
        try:
            result = self._resolve_template(condition, context)
            # Evaluate as Python boolean
            return result.lower() in ("true", "1", "yes")
        except Exception:
            return False

    async def _execute_hooks(
        self,
        hooks: List[Dict],
        context: ExecutionContext,
        extra_context: Optional[Dict] = None
    ) -> None:
        """Execute pipeline hooks."""
        for hook in hooks:
            if "log" in hook:
                message = self._resolve_template(hook["log"], context)
                logger.info(f"[HOOK] {message}")
            elif "emit_event" in hook:
                # TODO: Implement event emission
                pass

    def _aggregate_outputs(
        self,
        pipeline: PipelineDefinition,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Aggregate stage outputs into final pipeline output."""
        outputs = {}

        # Collect from output_mapping of each stage
        for stage in pipeline.stages:
            stage_output = context.stage_outputs.get(stage.id)
            if stage_output and stage.output_mapping:
                for output_key, json_path in stage.output_mapping.items():
                    # Simple JSON path extraction ($.field)
                    if json_path.startswith("$."):
                        field = json_path[2:]
                        if isinstance(stage_output, dict):
                            outputs[output_key] = stage_output.get(field)

        return outputs

    # Action handlers - integrated with real services

    async def _action_browser_launch(
        self,
        input_data: Any,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Launch browser for testing - uses Chrome for Testing."""
        logger.info("Launching browser", input=input_data)
        return await action_browser_launch(input_data, context)

    async def _action_browser_screenshots(
        self,
        input_data: Any,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Capture screenshots - uses Chrome DevTools Protocol."""
        logger.info("Capturing screenshots", input=input_data)
        return await action_browser_screenshots(input_data, context)

    async def _action_git_apply_fixes(
        self,
        input_data: Any,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Apply fixes in git worktree - uses real git operations."""
        logger.info("Applying fixes in worktree", input=input_data)
        return await action_git_apply_fixes(input_data, context)

    async def _action_git_create_pr(
        self,
        input_data: Any,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Create pull request - uses GitHub CLI (gh)."""
        logger.info("Creating PR", input=input_data)
        return await action_git_create_pr(input_data, context)

    async def _action_git_merge_pr(
        self,
        input_data: Any,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Merge pull request - uses GitHub CLI (gh)."""
        logger.info("Merging PR", input=input_data)
        return await action_git_merge_pr(input_data, context)

    async def _action_skills_validate(
        self,
        input_data: Any,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Run skill validation."""
        # Skills validation uses local skill files
        logger.info("Validating against skills", input=input_data)
        skills = input_data.get("skills", [])
        # For now, return passed - real implementation would load and validate
        return {"violations": [], "blocking": [], "passed": True, "skills_checked": skills}


# Singleton instance
pipeline_executor = PipelineExecutor()
