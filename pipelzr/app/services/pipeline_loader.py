"""
Pipeline Loader Service

Loads and parses YAML pipeline definitions.
Converts YAML to executable pipeline structures.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from jinja2 import Environment, BaseLoader, TemplateNotFound
import structlog

from .pipeline_validator import pipeline_validator, ValidationResult

logger = structlog.get_logger(__name__)


@dataclass
class StageDefinition:
    """Parsed stage definition."""
    id: str
    name: str
    stage_type: str  # "persona" or "action"
    persona: Optional[str] = None
    action: Optional[str] = None
    description: str = ""
    input_template: str = ""
    output_mapping: Dict[str, str] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    parallel_with: List[str] = field(default_factory=list)
    timeout_seconds: int = 120
    required: bool = True
    condition: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "stage_type": self.stage_type,
            "persona": self.persona,
            "action": self.action,
            "description": self.description,
            "input_template": self.input_template,
            "output_mapping": self.output_mapping,
            "depends_on": self.depends_on,
            "parallel_with": self.parallel_with,
            "timeout_seconds": self.timeout_seconds,
            "required": self.required,
            "condition": self.condition,
            "config": self.config
        }


@dataclass
class PipelineDefinition:
    """Parsed pipeline definition."""
    name: str
    display_name: str
    description: str
    version: str
    category: str
    stages: List[StageDefinition]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    config: Dict[str, Any]
    execution: Dict[str, Any]
    hooks: Dict[str, Any]
    raw_yaml: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "stages": [s.to_dict() for s in self.stages],
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "config": self.config,
            "execution": self.execution,
            "hooks": self.hooks
        }

    def get_execution_order(self) -> List[List[str]]:
        """Get stages in execution order (batches for parallel execution)."""
        # Use topological sort based on dependencies
        return self._topological_sort()

    def _topological_sort(self) -> List[List[str]]:
        """Topological sort stages into execution batches."""
        stage_map = {s.id: s for s in self.stages}
        remaining = set(s.id for s in self.stages)
        completed: set = set()
        batches: List[List[str]] = []

        while remaining:
            # Find stages with all dependencies satisfied
            batch: List[str] = []
            for stage_id in list(remaining):
                stage = stage_map[stage_id]
                deps_satisfied = all(d in completed for d in stage.depends_on)
                if deps_satisfied:
                    batch.append(stage_id)

            if not batch:
                # Circular dependency (should be caught by validator)
                raise ValueError(f"Circular dependency detected. Remaining: {remaining}")

            # Mark batch as completed
            for stage_id in batch:
                remaining.remove(stage_id)
                completed.add(stage_id)

            batches.append(batch)

        return batches


class PipelineLoader:
    """Loads and parses YAML pipeline definitions."""

    def __init__(self, pipelines_dir: Optional[str] = None):
        self.pipelines_dir = Path(pipelines_dir) if pipelines_dir else self._default_pipelines_dir()
        self.jinja_env = Environment(loader=BaseLoader())
        self._cache: Dict[str, PipelineDefinition] = {}

    def _default_pipelines_dir(self) -> Path:
        """Get default pipelines directory."""
        # Relative to this file: pipelzr/app/services/ -> pipelzr/pipelines/
        return Path(__file__).parent.parent.parent / "pipelines"

    async def load_from_file(
        self,
        filename: str,
        validate: bool = True,
        validate_credentials: bool = True
    ) -> tuple[PipelineDefinition, Optional[ValidationResult]]:
        """Load pipeline from file."""
        filepath = self.pipelines_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Pipeline file not found: {filepath}")

        logger.info("Loading pipeline from file", filepath=str(filepath))

        with open(filepath, "r") as f:
            yaml_content = f.read()

        return await self.load_from_yaml(
            yaml_content,
            validate=validate,
            validate_credentials=validate_credentials
        )

    async def load_from_yaml(
        self,
        yaml_content: str,
        validate: bool = True,
        validate_credentials: bool = True
    ) -> tuple[PipelineDefinition, Optional[ValidationResult]]:
        """Load pipeline from YAML content."""
        validation_result = None

        # Validate first if requested
        if validate:
            validation_result = await pipeline_validator.validate(
                yaml_content,
                validate_credentials=validate_credentials
            )
            if not validation_result.valid:
                logger.error(
                    "Pipeline validation failed",
                    error_count=len(validation_result.errors)
                )
                raise ValueError(f"Pipeline validation failed: {validation_result.errors}")

        # Parse YAML
        raw = yaml.safe_load(yaml_content)

        # Parse stages
        stages = self._parse_stages(raw.get("stages", []))

        # Build pipeline definition
        pipeline = PipelineDefinition(
            name=raw.get("name", "unnamed"),
            display_name=raw.get("display_name", raw.get("name", "Unnamed Pipeline")),
            description=raw.get("description", ""),
            version=raw.get("version", "1.0.0"),
            category=raw.get("category", "general"),
            stages=stages,
            input_schema=raw.get("input", {}),
            output_schema=raw.get("output", {}),
            config=raw.get("config", {}),
            execution=raw.get("execution", {}),
            hooks=raw.get("hooks", {}),
            raw_yaml=yaml_content
        )

        logger.info(
            "Pipeline loaded",
            name=pipeline.name,
            stage_count=len(pipeline.stages)
        )

        return pipeline, validation_result

    def _parse_stages(self, stages_raw: List[Dict]) -> List[StageDefinition]:
        """Parse stage definitions from raw YAML."""
        stages = []

        for raw in stages_raw:
            # Determine stage type
            if "persona" in raw:
                stage_type = "persona"
            elif raw.get("type") == "action":
                stage_type = "action"
            else:
                stage_type = "unknown"

            stage = StageDefinition(
                id=raw.get("id", ""),
                name=raw.get("name", ""),
                stage_type=stage_type,
                persona=raw.get("persona"),
                action=raw.get("action"),
                description=raw.get("description", ""),
                input_template=raw.get("input_template", ""),
                output_mapping=raw.get("output_mapping", {}),
                depends_on=raw.get("depends_on", []),
                parallel_with=raw.get("parallel_with", []),
                timeout_seconds=raw.get("timeout_seconds", 120),
                required=raw.get("required", True),
                condition=raw.get("condition"),
                config=raw.get("config", {})
            )
            stages.append(stage)

        return stages

    def list_available_pipelines(self) -> List[Dict[str, Any]]:
        """List all available pipeline files."""
        pipelines = []

        if not self.pipelines_dir.exists():
            logger.warning("Pipelines directory not found", path=str(self.pipelines_dir))
            return pipelines

        for filepath in self.pipelines_dir.glob("*.yaml"):
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                raw = yaml.safe_load(content)

                pipelines.append({
                    "filename": filepath.name,
                    "name": raw.get("name", filepath.stem),
                    "display_name": raw.get("display_name", raw.get("name", filepath.stem)),
                    "description": raw.get("description", "")[:200],
                    "version": raw.get("version", "1.0.0"),
                    "category": raw.get("category", "general"),
                    "stage_count": len(raw.get("stages", []))
                })
            except Exception as e:
                logger.warning("Failed to parse pipeline file", filepath=str(filepath), error=str(e))

        # Also check .yml extension
        for filepath in self.pipelines_dir.glob("*.yml"):
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                raw = yaml.safe_load(content)

                pipelines.append({
                    "filename": filepath.name,
                    "name": raw.get("name", filepath.stem),
                    "display_name": raw.get("display_name", raw.get("name", filepath.stem)),
                    "description": raw.get("description", "")[:200],
                    "version": raw.get("version", "1.0.0"),
                    "category": raw.get("category", "general"),
                    "stage_count": len(raw.get("stages", []))
                })
            except Exception as e:
                logger.warning("Failed to parse pipeline file", filepath=str(filepath), error=str(e))

        return pipelines

    def get_pipeline_definition(self, name: str) -> Optional[Dict[str, Any]]:
        """Get raw pipeline definition by name (without loading/validating)."""
        # Try exact filename first
        for ext in [".yaml", ".yml"]:
            filepath = self.pipelines_dir / f"{name}{ext}"
            if filepath.exists():
                with open(filepath, "r") as f:
                    return yaml.safe_load(f.read())

        # Try matching by pipeline name field
        for filepath in self.pipelines_dir.glob("*.yaml"):
            try:
                with open(filepath, "r") as f:
                    raw = yaml.safe_load(f.read())
                if raw.get("name") == name:
                    return raw
            except Exception:
                continue

        return None

    def clear_cache(self) -> None:
        """Clear the pipeline cache."""
        self._cache.clear()


# Singleton instance
pipeline_loader = PipelineLoader()
