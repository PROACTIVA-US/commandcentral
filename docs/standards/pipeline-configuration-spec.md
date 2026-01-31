---
title: Pipeline Configuration Standard
version: 1.0.0
created: 2026-01-31
status: active
---

# Pipeline Configuration Standard

Pipeline configuration defines HOW and WHERE a pipeline executes tasks. This is critical for multi-repo scenarios where the orchestrator (PIPELZR) runs in one repo but executes work in another.

## Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum

class ExecutionMode(str, Enum):
    LOCAL = "local"           # Execute in same process
    WORKTREE = "worktree"     # Execute in git worktree
    CONTAINER = "container"   # Execute in Docker container

class PipelineConfig(BaseModel):
    # REQUIRED: Target repository
    target_repo: str = Field(
        ...,
        description="Absolute path or URL to target repository. MUST be explicit."
    )
    target_branch: str = Field(
        default="main",
        description="Branch to create feature branches from"
    )

    # Working directories
    worktree_root: str = Field(
        ...,
        description="Directory for git worktrees. Must be outside target_repo."
    )

    # Skill and knowledge sources
    skills_source: str = Field(
        ...,
        description="Path to skills directory or API endpoint"
    )
    knowledge_source: str = Field(
        ...,
        description="Path to self-documentation directory"
    )

    # Execution context
    execution_context: Dict = Field(
        default_factory=dict,
        description="Service-specific context for agents"
    )

    # Execution mode
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.WORKTREE,
        description="How to isolate task execution"
    )

    # Validation
    pre_validation: List[str] = Field(
        default_factory=list,
        description="Validation checks before task execution"
    )
    post_validation: List[str] = Field(
        default_factory=list,
        description="Validation checks after task execution"
    )
```

## JSON Configuration Example

```json
{
  "spec_path": "/Users/danielconnolly/Projects/CommandCentral/docs/specs/commandcentral-frontend.md",
  "target_repo": "file:///Users/danielconnolly/Projects/CommandCentral",
  "target_branch": "main",
  "worktree_root": "/tmp/commandcentral-worktrees",
  "skills_source": "file:///Users/danielconnolly/Projects/CommandCentral/docs/self/skills",
  "knowledge_source": "file:///Users/danielconnolly/Projects/CommandCentral/docs/self",
  "execution_context": {
    "service": "commandcentral",
    "port": 8000,
    "tech_stack": ["react", "typescript", "tailwind", "shadcn", "zustand"],
    "api_base": "http://localhost:8000/api/v1"
  },
  "execution_mode": "worktree",
  "pre_validation": [
    "target_repo_exists",
    "skills_source_readable",
    "knowledge_source_readable"
  ],
  "post_validation": [
    "typescript_compiles",
    "eslint_passes",
    "tests_pass"
  ]
}
```

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `target_repo` | string | **REQUIRED**. Must be absolute path or URL. No defaults. |
| `worktree_root` | string | **REQUIRED**. Directory for isolated workspaces. |
| `skills_source` | string | **REQUIRED**. Where to find skill definitions. |
| `knowledge_source` | string | **REQUIRED**. Where to find self-documentation. |

## Source URI Formats

```
file:///absolute/path          # Local filesystem
http://localhost:8001/api/v1   # Local service API
https://github.com/org/repo    # Remote repository
```

## Execution Context

The `execution_context` object provides service-specific information:

```json
{
  "service": "commandcentral",
  "port": 8000,
  "tech_stack": ["react", "typescript", "tailwind", "shadcn", "zustand"],
  "api_base": "http://localhost:8000/api/v1",
  "test_command": "npm test",
  "lint_command": "npm run lint",
  "build_command": "npm run build",
  "env_vars": {
    "VITE_API_URL": "http://localhost:8000"
  }
}
```

## Validation Checks

### Pre-validation (before execution)

| Check | Description |
|-------|-------------|
| `target_repo_exists` | Verify target repo path/URL is accessible |
| `target_branch_exists` | Verify base branch exists |
| `skills_source_readable` | Verify skills can be loaded |
| `knowledge_source_readable` | Verify docs can be loaded |
| `worktree_root_writable` | Verify worktree directory is writable |

### Post-validation (after execution)

| Check | Description |
|-------|-------------|
| `typescript_compiles` | Run `tsc --noEmit` |
| `eslint_passes` | Run `npm run lint` |
| `tests_pass` | Run `npm test` |
| `build_succeeds` | Run `npm run build` |
| `no_security_vulns` | Run `npm audit` |

## Migration from CC4

Current CC4 pipeline config (implicit):
```python
# CC4 defaults (WRONG for cross-repo work)
target_repo = "."  # Current directory
worktree_root = "./worktrees"
skills_source = "./skills"  # Doesn't exist!
knowledge_source = "./docs"  # CC4's docs, not target service
```

New required config (explicit):
```python
# CommandCentral frontend build (CORRECT)
target_repo = "/Users/danielconnolly/Projects/CommandCentral"
worktree_root = "/tmp/commandcentral-worktrees"
skills_source = "/Users/danielconnolly/Projects/CommandCentral/docs/self/skills"
knowledge_source = "/Users/danielconnolly/Projects/CommandCentral/docs/self"
```

## PIPELZR API

When PIPELZR receives a pipeline execution request:

```http
POST /api/v1/pipelines/execute
Content-Type: application/json

{
  "spec_path": "/path/to/spec.md",
  "config": {
    "target_repo": "...",
    "worktree_root": "...",
    "skills_source": "...",
    "knowledge_source": "...",
    "execution_context": {...}
  }
}
```

Response:
```json
{
  "pipeline_id": "uuid",
  "status": "running",
  "config_validated": true,
  "target_repo": "/path/to/CommandCentral",
  "worktree": "/tmp/commandcentral-worktrees/pipeline-uuid"
}
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `E001` | target_repo not specified | Add explicit target_repo |
| `E002` | target_repo not found | Check path/URL |
| `E003` | skills_source not found | Create /docs/self/skills |
| `E004` | knowledge_source not found | Create /docs/self |
| `E005` | worktree_root not writable | Check permissions |
