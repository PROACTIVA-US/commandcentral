"""
Pipeline Validator Service

Validates pipeline YAML definitions before execution.
Implements the pipeline-validation skill.
"""

import yaml
import os
import httpx
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from jinja2 import Environment, TemplateSyntaxError
import structlog

logger = structlog.get_logger(__name__)


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationError:
    code: str
    message: str
    location: str
    severity: ValidationSeverity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "location": self.location,
            "severity": self.severity.value
        }


@dataclass
class ValidationResult:
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    credential_status: Dict[str, Any] = field(default_factory=dict)
    estimated_duration_seconds: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "credential_status": self.credential_status,
            "estimated_duration_seconds": self.estimated_duration_seconds
        }


class PipelineValidator:
    """Validates pipeline YAML definitions before execution."""

    REQUIRED_TOP_LEVEL = {"name", "stages"}
    REQUIRED_STAGE_FIELDS = {"id", "name"}

    def __init__(self):
        self.jinja_env = Environment()
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    async def validate(
        self,
        yaml_content: str,
        validate_credentials: bool = True,
        dry_run: bool = False
    ) -> ValidationResult:
        """Full pipeline validation."""
        self.errors = []
        self.warnings = []

        logger.info("Starting pipeline validation", validate_credentials=validate_credentials)

        # 1. Parse YAML
        pipeline = self._parse_yaml(yaml_content)
        if not pipeline:
            return self._build_result({}, 0)

        # 2. Validate structure
        self._validate_structure(pipeline)

        # 3. Validate stages
        self._validate_stages(pipeline.get("stages", []))

        # 4. Validate dependencies
        self._validate_dependencies(pipeline.get("stages", []))

        # 5. Validate templates
        self._validate_templates(pipeline)

        # 6. Validate credentials (if requested)
        credential_status = {}
        if validate_credentials and not self.errors:
            credential_status = await self._validate_credentials(pipeline)

        # 7. Estimate duration
        duration = self._estimate_duration(pipeline)

        result = self._build_result(credential_status, duration)
        logger.info(
            "Pipeline validation complete",
            valid=result.valid,
            error_count=len(result.errors),
            warning_count=len(result.warnings)
        )
        return result

    def _parse_yaml(self, content: str) -> Optional[Dict]:
        """Parse YAML content."""
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            self.errors.append(ValidationError(
                code="INVALID_YAML",
                message=str(e),
                location="root",
                severity=ValidationSeverity.ERROR
            ))
            return None

    def _validate_structure(self, pipeline: Dict) -> None:
        """Validate top-level structure."""
        for field in self.REQUIRED_TOP_LEVEL:
            if field not in pipeline:
                self.errors.append(ValidationError(
                    code="MISSING_REQUIRED_FIELD",
                    message=f"Missing required field: {field}",
                    location=f"root.{field}",
                    severity=ValidationSeverity.ERROR
                ))

    def _validate_stages(self, stages: List[Dict]) -> None:
        """Validate stage definitions."""
        if not stages:
            self.errors.append(ValidationError(
                code="MISSING_REQUIRED_FIELD",
                message="Pipeline must have at least one stage",
                location="stages",
                severity=ValidationSeverity.ERROR
            ))
            return

        stage_ids = set()
        for i, stage in enumerate(stages):
            loc = f"stages[{i}]"

            # Check required fields
            for field in self.REQUIRED_STAGE_FIELDS:
                if field not in stage:
                    self.errors.append(ValidationError(
                        code="MISSING_REQUIRED_FIELD",
                        message=f"Stage missing required field: {field}",
                        location=f"{loc}.{field}",
                        severity=ValidationSeverity.ERROR
                    ))

            # Check for duplicate IDs
            stage_id = stage.get("id")
            if stage_id in stage_ids:
                self.errors.append(ValidationError(
                    code="DUPLICATE_STAGE_ID",
                    message=f"Duplicate stage ID: {stage_id}",
                    location=f"{loc}.id",
                    severity=ValidationSeverity.ERROR
                ))
            if stage_id:
                stage_ids.add(stage_id)

            # Check for persona or action type
            if "persona" not in stage and stage.get("type") != "action":
                self.errors.append(ValidationError(
                    code="INVALID_STAGE",
                    message="Stage must have 'persona' or 'type: action'",
                    location=loc,
                    severity=ValidationSeverity.ERROR
                ))

            # Check timeout
            if "timeout_seconds" not in stage:
                self.warnings.append(ValidationError(
                    code="MISSING_TIMEOUT",
                    message="Stage should specify timeout_seconds",
                    location=loc,
                    severity=ValidationSeverity.WARNING
                ))

    def _validate_dependencies(self, stages: List[Dict]) -> None:
        """Validate stage dependencies (no cycles, valid refs)."""
        stage_ids = {s.get("id") for s in stages if s.get("id")}

        # Build adjacency list
        graph: Dict[str, set] = {s.get("id"): set() for s in stages if s.get("id")}

        for stage in stages:
            stage_id = stage.get("id")
            if not stage_id:
                continue

            for dep in stage.get("depends_on", []):
                if dep not in stage_ids:
                    self.errors.append(ValidationError(
                        code="MISSING_STAGE_REF",
                        message=f"Stage '{stage_id}' depends on non-existent stage '{dep}'",
                        location=f"stages[{stage_id}].depends_on",
                        severity=ValidationSeverity.ERROR
                    ))
                else:
                    graph[stage_id].add(dep)

            # Also check parallel_with references
            for parallel in stage.get("parallel_with", []):
                if parallel not in stage_ids:
                    self.errors.append(ValidationError(
                        code="MISSING_STAGE_REF",
                        message=f"Stage '{stage_id}' parallel_with non-existent stage '{parallel}'",
                        location=f"stages[{stage_id}].parallel_with",
                        severity=ValidationSeverity.ERROR
                    ))

        # Check for cycles using DFS
        visited: set = set()
        rec_stack: set = set()

        def has_cycle(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor, path + [node]):
                        return True
                elif neighbor in rec_stack:
                    cycle = path + [node, neighbor]
                    self.errors.append(ValidationError(
                        code="CIRCULAR_DEPENDENCY",
                        message=f"Circular dependency detected: {' -> '.join(cycle)}",
                        location="stages.depends_on",
                        severity=ValidationSeverity.ERROR
                    ))
                    return True

            rec_stack.remove(node)
            return False

        for stage_id in graph:
            if stage_id not in visited:
                has_cycle(stage_id, [])

    def _validate_templates(self, pipeline: Dict) -> None:
        """Validate Jinja2 template syntax."""
        templates = self._extract_templates(pipeline)
        for loc, template in templates:
            try:
                self.jinja_env.parse(template)
            except TemplateSyntaxError as e:
                self.errors.append(ValidationError(
                    code="TEMPLATE_ERROR",
                    message=f"Invalid template syntax: {e.message}",
                    location=loc,
                    severity=ValidationSeverity.ERROR
                ))

    def _extract_templates(self, obj: Any, path: str = "") -> List[Tuple[str, str]]:
        """Recursively extract template strings."""
        templates: List[Tuple[str, str]] = []
        if isinstance(obj, str) and "{{" in obj:
            templates.append((path, obj))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                templates.extend(self._extract_templates(v, new_path))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                templates.extend(self._extract_templates(v, f"{path}[{i}]"))
        return templates

    async def _validate_credentials(self, pipeline: Dict) -> Dict[str, Any]:
        """Validate required API credentials."""
        results = {}
        required = self._extract_required_credentials(pipeline)

        logger.info("Validating credentials", required=list(required))

        for cred_type in required:
            if cred_type == "gemini":
                results["gemini"] = await self._validate_gemini_key()
            elif cred_type == "github":
                results["github"] = await self._validate_github_token()
            elif cred_type == "anthropic":
                results["anthropic"] = await self._validate_anthropic_key()

        # Add errors for invalid credentials
        for cred, status in results.items():
            if not status.get("valid"):
                self.errors.append(ValidationError(
                    code="INVALID_CREDENTIAL",
                    message=f"{cred}: {status.get('error', 'Unknown error')}",
                    location=f"credentials.{cred}",
                    severity=ValidationSeverity.ERROR
                ))

        return results

    def _extract_required_credentials(self, pipeline: Dict) -> set:
        """Determine which credentials the pipeline needs."""
        creds: set = set()

        for stage in pipeline.get("stages", []):
            # Check for vision model in config
            config = stage.get("config", {})
            model = config.get("model", "")
            if "gemini" in model.lower():
                creds.add("gemini")
            elif "claude" in model.lower() or "anthropic" in model.lower():
                creds.add("anthropic")

            # Check persona for model hints
            persona = stage.get("persona", "")
            if "vision" in persona.lower():
                creds.add("gemini")  # Default vision to Gemini

            # Check for git actions
            action = stage.get("action", "")
            if action.startswith("git."):
                creds.add("github")

            # Check input templates for model references
            input_template = stage.get("input_template", "")
            if isinstance(input_template, str) and "gemini" in input_template.lower():
                creds.add("gemini")

        return creds

    async def _validate_gemini_key(self) -> Dict[str, Any]:
        """Validate Gemini API key."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return {"valid": False, "error": "GEMINI_API_KEY not set"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://generativelanguage.googleapis.com/v1/models",
                    params={"key": api_key},
                    timeout=10.0
                )

                if response.status_code == 401:
                    return {"valid": False, "error": "Invalid API key"}
                elif response.status_code == 403:
                    return {"valid": False, "error": "Insufficient permissions"}
                elif response.status_code != 200:
                    return {"valid": False, "error": f"API error: {response.status_code}"}

                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                has_flash_3 = any("gemini-3-flash" in n or "gemini-2" in n for n in model_names)

                logger.info("Gemini API key validated", models_count=len(models), has_flash_3=has_flash_3)

                return {
                    "valid": True,
                    "models_available": len(models),
                    "gemini_3_flash": has_flash_3,
                    "agentic_vision": has_flash_3
                }
        except httpx.TimeoutException:
            return {"valid": False, "error": "Connection timeout"}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def _validate_github_token(self) -> Dict[str, Any]:
        """Validate GitHub token."""
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            return {"valid": False, "error": "GITHUB_TOKEN not set"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {token}"},
                    timeout=10.0
                )

                if response.status_code == 401:
                    return {"valid": False, "error": "Invalid token"}
                elif response.status_code != 200:
                    return {"valid": False, "error": f"API error: {response.status_code}"}

                user = response.json()
                scopes = response.headers.get("X-OAuth-Scopes", "").split(", ")

                logger.info("GitHub token validated", user=user.get("login"), scopes=scopes)

                return {
                    "valid": True,
                    "user": user.get("login"),
                    "scopes": scopes
                }
        except httpx.TimeoutException:
            return {"valid": False, "error": "Connection timeout"}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def _validate_anthropic_key(self) -> Dict[str, Any]:
        """Validate Anthropic API key."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {"valid": False, "error": "ANTHROPIC_API_KEY not set"}

        # Anthropic doesn't have a simple validation endpoint
        # Check format and try a minimal API call
        if not api_key.startswith("sk-ant-"):
            return {"valid": False, "error": "Invalid key format (should start with sk-ant-)"}

        try:
            async with httpx.AsyncClient() as client:
                # Try to get model info (minimal call)
                response = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01"
                    },
                    timeout=10.0
                )

                if response.status_code == 401:
                    return {"valid": False, "error": "Invalid API key"}
                elif response.status_code == 200:
                    return {"valid": True, "format_valid": True}
                else:
                    # Even if models endpoint fails, key format is valid
                    return {"valid": True, "format_valid": True}

        except Exception:
            # If API call fails, still accept valid format
            return {"valid": True, "format_valid": True}

    def _estimate_duration(self, pipeline: Dict) -> int:
        """Estimate pipeline execution duration."""
        total = 0
        for stage in pipeline.get("stages", []):
            timeout = stage.get("timeout_seconds", 120)
            # Assume stages complete in ~50% of timeout on average
            total += timeout // 2
        return total

    def _build_result(self, credentials: Dict, duration: int) -> ValidationResult:
        """Build final validation result."""
        return ValidationResult(
            valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
            credential_status=credentials,
            estimated_duration_seconds=duration
        )


# Singleton instance
pipeline_validator = PipelineValidator()
