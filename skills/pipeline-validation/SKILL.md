---
name: pipeline-validation
priority: P0
enforcement: blocking
keywords:
  - pipeline, yaml, validation, schema
  - stages, dependencies, execution
  - api key, credentials, secrets
file_patterns:
  - "pipelzr/pipelines/**/*.yaml"
  - "pipelzr/pipelines/**/*.yml"
---

# Pipeline Validation Skill

> **Type:** Validation Skill (P0 - Blocking)
> **Purpose:** Validate pipeline YAML before execution

---

## Overview

This skill validates pipeline definitions and execution prerequisites before allowing pipeline execution. It performs:

1. **Schema Validation** - YAML structure matches pipeline schema
2. **Dependency Validation** - No circular dependencies, all refs exist
3. **API Key Validation** - Required credentials are present and valid
4. **Resource Validation** - Required services/tools are available

---

## Contract

### Inputs

```yaml
inputs:
  pipeline_yaml:
    type: string
    description: Raw YAML content or path to pipeline file
    required: true
  validate_credentials:
    type: boolean
    description: Whether to validate API keys/credentials
    default: true
  dry_run:
    type: boolean
    description: Simulate execution without running
    default: false
```

### Outputs

```yaml
outputs:
  valid:
    type: boolean
    description: Whether pipeline passed all validation
  errors:
    type: array
    items:
      type: object
      properties:
        code: string      # Error code (e.g., INVALID_SCHEMA, CIRCULAR_DEP)
        message: string   # Human-readable error
        location: string  # YAML path (e.g., stages[2].depends_on)
        severity: string  # error | warning
  warnings:
    type: array
    description: Non-blocking issues found
  credential_status:
    type: object
    description: Status of each required credential
  estimated_duration_seconds:
    type: integer
    description: Estimated execution time based on stages
```

### Errors

```yaml
errors:
  INVALID_YAML:
    description: YAML parsing failed
    severity: error
  MISSING_REQUIRED_FIELD:
    description: Required field not present
    severity: error
  INVALID_SCHEMA:
    description: Field type or structure incorrect
    severity: error
  CIRCULAR_DEPENDENCY:
    description: Stages have circular depends_on
    severity: error
  MISSING_STAGE_REF:
    description: depends_on references non-existent stage
    severity: error
  INVALID_CREDENTIAL:
    description: API key missing or invalid
    severity: error
  CREDENTIAL_EXPIRED:
    description: API key is expired
    severity: error
  SERVICE_UNAVAILABLE:
    description: Required service not reachable
    severity: error
  TEMPLATE_ERROR:
    description: Jinja2 template syntax error
    severity: error
```

---

## Validation Rules

### P0 Rules (Blocking - Must Pass)

#### 1. Valid YAML Structure
```python
# Pipeline must parse as valid YAML
try:
    pipeline = yaml.safe_load(content)
except yaml.YAMLError as e:
    raise ValidationError("INVALID_YAML", str(e))
```

#### 2. Required Top-Level Fields
```yaml
required_fields:
  - name          # Pipeline identifier
  - stages        # At least one stage
```

#### 3. Stage Structure
```yaml
stage_required:
  - id            # Unique stage identifier
  - name          # Display name
  # Plus ONE of:
  - persona       # For LLM stages
  - type: action  # For action stages
```

#### 4. No Circular Dependencies
```python
# Topological sort must succeed
def validate_no_cycles(stages):
    graph = build_dependency_graph(stages)
    try:
        topological_sort(graph)
    except CycleDetected as e:
        raise ValidationError("CIRCULAR_DEPENDENCY", e.cycle)
```

#### 5. Valid Stage References
```python
# All depends_on/parallel_with references must exist
stage_ids = {s['id'] for s in stages}
for stage in stages:
    for dep in stage.get('depends_on', []):
        if dep not in stage_ids:
            raise ValidationError("MISSING_STAGE_REF", dep)
```

#### 6. Valid Template Syntax
```python
# All Jinja2 templates must be syntactically correct
from jinja2 import Environment, TemplateSyntaxError
env = Environment()
for template_str in extract_templates(pipeline):
    try:
        env.parse(template_str)
    except TemplateSyntaxError as e:
        raise ValidationError("TEMPLATE_ERROR", str(e))
```

### P1 Rules (Required - Should Pass)

#### 7. Input/Output Schema Defined
```yaml
# Pipeline should declare input/output schemas
recommended:
  - input.type: object
  - input.properties: defined
  - output.type: object
```

#### 8. Timeout Specified
```yaml
# Stages should have explicit timeouts
stage_recommended:
  - timeout_seconds: > 0
```

#### 9. Hooks Defined
```yaml
# Pipeline should have error handling hooks
recommended_hooks:
  - on_failure
```

---

## Credential Validation

### Supported Credential Types

| Credential | Environment Variable | Validation Method |
|------------|---------------------|-------------------|
| Gemini API | `GEMINI_API_KEY` | Test API call |
| OpenAI API | `OPENAI_API_KEY` | Test API call |
| Anthropic API | `ANTHROPIC_API_KEY` | Test API call |
| GitHub Token | `GITHUB_TOKEN` | Test API call |
| Google Cloud | `GOOGLE_APPLICATION_CREDENTIALS` | ADC check |

### Validation Process

```python
async def validate_credentials(pipeline: dict) -> dict:
    """Validate all credentials required by pipeline stages."""
    results = {}

    # Extract required credentials from stage configs
    required = extract_required_credentials(pipeline)

    for cred_type in required:
        validator = CREDENTIAL_VALIDATORS[cred_type]
        try:
            result = await validator.validate()
            results[cred_type] = {
                "valid": True,
                "expires_at": result.expires_at,
                "scopes": result.scopes
            }
        except CredentialError as e:
            results[cred_type] = {
                "valid": False,
                "error": str(e),
                "code": e.code
            }

    return results
```

### Gemini API Validation

```python
async def validate_gemini_api_key() -> CredentialResult:
    """Validate Gemini API key with a minimal test call."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise CredentialError("MISSING_CREDENTIAL", "GEMINI_API_KEY not set")

    # Test with minimal API call
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://generativelanguage.googleapis.com/v1/models",
            params={"key": api_key}
        )

        if response.status_code == 401:
            raise CredentialError("INVALID_CREDENTIAL", "Gemini API key invalid")
        elif response.status_code == 403:
            raise CredentialError("INSUFFICIENT_PERMISSIONS", "API key lacks required scopes")
        elif response.status_code != 200:
            raise CredentialError("API_ERROR", f"Unexpected status: {response.status_code}")

        # Check for Gemini 3 Flash availability
        models = response.json().get("models", [])
        has_flash = any("gemini-3-flash" in m.get("name", "") for m in models)

        return CredentialResult(
            valid=True,
            model_access=["gemini-3-flash-preview"] if has_flash else [],
            agentic_vision_available=has_flash
        )
```

---

## Implementation

### Python Implementation

```python
# pipelzr/app/services/pipeline_validator.py

import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import httpx
import os
from jinja2 import Environment, TemplateSyntaxError

class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"

@dataclass
class ValidationError:
    code: str
    message: str
    location: str
    severity: ValidationSeverity

@dataclass
class ValidationResult:
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    credential_status: Dict[str, Any]
    estimated_duration_seconds: int

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

        return self._build_result(credential_status, duration)

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
        stage_ids = {s.get("id") for s in stages}

        # Build adjacency list
        graph = {s.get("id"): set() for s in stages}
        for stage in stages:
            stage_id = stage.get("id")
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

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
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

    def _extract_templates(self, obj: Any, path: str = "") -> List[tuple]:
        """Recursively extract template strings."""
        templates = []
        if isinstance(obj, str) and "{{" in obj:
            templates.append((path, obj))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                templates.extend(self._extract_templates(v, f"{path}.{k}"))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                templates.extend(self._extract_templates(v, f"{path}[{i}]"))
        return templates

    async def _validate_credentials(self, pipeline: Dict) -> Dict[str, Any]:
        """Validate required API credentials."""
        results = {}
        required = self._extract_required_credentials(pipeline)

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
        creds = set()

        for stage in pipeline.get("stages", []):
            # Check for vision model
            config = stage.get("config", {})
            model = config.get("model", "")
            if "gemini" in model.lower():
                creds.add("gemini")
            elif "claude" in model.lower() or "anthropic" in model.lower():
                creds.add("anthropic")

            # Check for git actions
            action = stage.get("action", "")
            if action.startswith("git."):
                creds.add("github")

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
                has_flash_3 = any("gemini-3-flash" in n for n in model_names)

                return {
                    "valid": True,
                    "models_available": len(models),
                    "gemini_3_flash": has_flash_3,
                    "agentic_vision": has_flash_3
                }
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
                return {
                    "valid": True,
                    "user": user.get("login"),
                    "scopes": response.headers.get("X-OAuth-Scopes", "").split(", ")
                }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def _validate_anthropic_key(self) -> Dict[str, Any]:
        """Validate Anthropic API key."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {"valid": False, "error": "ANTHROPIC_API_KEY not set"}

        # Anthropic doesn't have a simple validation endpoint
        # Just check format
        if not api_key.startswith("sk-ant-"):
            return {"valid": False, "error": "Invalid key format"}

        return {"valid": True, "format_valid": True}

    def _estimate_duration(self, pipeline: Dict) -> int:
        """Estimate pipeline execution duration."""
        total = 0
        for stage in pipeline.get("stages", []):
            timeout = stage.get("timeout_seconds", 120)
            # Assume stages complete in ~50% of timeout
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
```

---

## Usage

### Via API

```bash
# Validate pipeline YAML
curl -X POST http://localhost:9005/api/v1/pipelines/validate \
  -H "Content-Type: application/json" \
  -d '{
    "yaml_content": "...",
    "validate_credentials": true
  }'
```

### Response

```json
{
  "valid": false,
  "errors": [
    {
      "code": "INVALID_CREDENTIAL",
      "message": "gemini: GEMINI_API_KEY not set",
      "location": "credentials.gemini",
      "severity": "error"
    }
  ],
  "warnings": [
    {
      "code": "MISSING_TIMEOUT",
      "message": "Stage should specify timeout_seconds",
      "location": "stages[3]",
      "severity": "warning"
    }
  ],
  "credential_status": {
    "gemini": {
      "valid": false,
      "error": "GEMINI_API_KEY not set"
    }
  },
  "estimated_duration_seconds": 450
}
```

---

## Integration Points

1. **Pre-execution hook**: Automatically validate before `execute_pipeline()`
2. **Pipeline loader**: Validate when loading YAML from file
3. **API endpoint**: Expose `/api/v1/pipelines/validate` for manual checks
4. **CI/CD**: Can be run as pre-commit hook for pipeline YAML files

---

## Related Skills

- `ux-governance` - UX validation rules (invoked by pipelines)
- `ui-design-validation` - UI validation rules (invoked by pipelines)
- `skill-governance` - Skill quality validation
