---
title: PIPELZR Enhancement Plan
version: 1.0.0
created: 2026-01-31
status: proposed
priority: high
---

# PIPELZR Enhancement Plan

## Executive Summary

PIPELZR must evolve from a simple task runner to the **central orchestrator** for multi-repo development work. This document outlines the enhancements needed to support skill resolution, knowledge aggregation, and cross-repo execution.

---

## Current State

PIPELZR currently:
- Manages tasks and pipelines
- Executes agent work in CC4's context
- Has no skill resolution capability
- Has no knowledge aggregation capability
- Cannot target external repositories

## Target State

PIPELZR will:
- Resolve skills from target service's `/docs/self/skills/`
- Aggregate knowledge from target service's `/docs/self/`
- Execute work in isolated worktrees of the target repository
- Support multi-repo pipelines

---

## New Components

### 1. Skill Resolver Service

**Location:** `/backend/app/services/skill_resolver.py`

**Purpose:** Match tasks to skills and load skill definitions.

```python
class SkillResolver:
    """Resolves skills from service self-documentation."""

    async def resolve(
        self,
        task_description: str,
        target_service: str,
        skills_source: str,
    ) -> list[SkillDefinition]:
        """
        Find skills matching the task description.

        1. Load manifest.json from skills_source
        2. Match task against trigger patterns
        3. Score and rank matches
        4. Return top matching skills
        """
        pass

    async def load_skill(
        self,
        skill_name: str,
        skills_source: str,
    ) -> SkillDefinition:
        """Load a specific skill definition."""
        pass

    def score_match(
        self,
        task_description: str,
        triggers: list[TriggerPattern],
    ) -> float:
        """Score how well triggers match the task."""
        pass
```

**API Endpoint:**

```http
GET /api/v1/skills/resolve?task={description}&service={name}
```

### 2. Knowledge Aggregator Service

**Location:** `/backend/app/services/knowledge_aggregator.py`

**Purpose:** Gather context from service self-documentation.

```python
class KnowledgeAggregator:
    """Aggregates knowledge from service documentation."""

    async def gather_context(
        self,
        skill: SkillDefinition,
        knowledge_source: str,
    ) -> AgentContext:
        """
        Gather all context required by a skill.

        1. Load api-reference.md sections from context_required.api_reference
        2. Load domain-model.md sections from context_required.domain_models
        3. Load patterns.md sections from context_required.patterns
        4. Combine into structured agent context
        """
        pass

    async def load_api_reference(
        self,
        knowledge_source: str,
        endpoints: list[str],
    ) -> str:
        """Load specific API endpoint documentation."""
        pass

    async def load_domain_models(
        self,
        knowledge_source: str,
        models: list[str],
    ) -> str:
        """Load specific domain model documentation."""
        pass
```

**API Endpoint:**

```http
GET /api/v1/knowledge/context?service={name}&skill={name}
```

### 3. Multi-Repo Executor

**Location:** `/backend/app/services/multi_repo_executor.py`

**Purpose:** Execute tasks in target repository worktrees.

```python
class MultiRepoExecutor:
    """Executes tasks in isolated worktrees of target repositories."""

    async def execute(
        self,
        task: Task,
        config: PipelineConfig,
    ) -> ExecutionResult:
        """
        Execute a task in the target repository.

        1. Validate config (target_repo, worktree_root exist)
        2. Create isolated worktree
        3. Load skills for task
        4. Gather knowledge context
        5. Execute agent with skill + knowledge
        6. Validate outputs
        7. Cleanup or prepare for PR
        """
        pass

    async def create_worktree(
        self,
        target_repo: str,
        worktree_root: str,
        branch_name: str,
    ) -> str:
        """Create git worktree for isolated execution."""
        pass

    async def validate_outputs(
        self,
        worktree_path: str,
        skill: SkillDefinition,
    ) -> ValidationResult:
        """Run validation checks from skill definition."""
        pass
```

### 4. Pipeline Config Validator

**Location:** `/backend/app/services/config_validator.py`

**Purpose:** Validate pipeline configurations before execution.

```python
class ConfigValidator:
    """Validates pipeline configurations."""

    async def validate(self, config: PipelineConfig) -> ValidationResult:
        """
        Validate all configuration fields.

        Checks:
        - target_repo exists and is git repo
        - worktree_root is writable
        - skills_source is readable
        - knowledge_source is readable
        - execution_context has required fields
        """
        pass

    def check_target_repo(self, path: str) -> tuple[bool, str]:
        """Verify target_repo is valid git repository."""
        pass

    def check_skills_source(self, path: str) -> tuple[bool, str]:
        """Verify skills can be loaded."""
        pass
```

---

## New API Endpoints

### Skills API

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/skills/resolve | Match task to skills |
| GET | /api/v1/skills/{name} | Get skill definition |
| GET | /api/v1/skills | List all skills (with optional service filter) |

### Knowledge API

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/knowledge/context | Get aggregated context for skill |
| GET | /api/v1/knowledge/api-reference | Get API docs for endpoints |
| GET | /api/v1/knowledge/domain-models | Get domain model docs |

### Pipeline Execution API

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/pipelines/execute | Execute pipeline with config |
| POST | /api/v1/pipelines/validate-config | Validate config without executing |
| GET | /api/v1/pipelines/{id}/worktree | Get worktree status |

---

## Data Models

### SkillDefinition

```python
class SkillDefinition(BaseModel):
    name: str
    version: str
    domain: str
    category: str
    description: str
    triggers: list[TriggerPattern]
    context_required: ContextRequirements
    outputs: list[ExpectedOutput]
    preconditions: list[Precondition]
    instructions: list[Instruction]
    validation: list[ValidationCheck]
    examples: list[Example]
```

### AgentContext

```python
class AgentContext(BaseModel):
    skill: SkillDefinition
    api_reference: str  # Relevant API docs
    domain_models: str  # Relevant model docs
    patterns: str       # Relevant pattern docs
    dependencies: list[str]
    execution_context: dict  # From pipeline config
```

### PipelineConfig

```python
class PipelineConfig(BaseModel):
    target_repo: str          # REQUIRED
    target_branch: str = "main"
    worktree_root: str        # REQUIRED
    skills_source: str        # REQUIRED
    knowledge_source: str     # REQUIRED
    execution_context: dict   # Service-specific context
    execution_mode: str = "worktree"
    pre_validation: list[str]
    post_validation: list[str]
```

---

## Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Pipeline Execution Flow                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Receive Pipeline Request                                            │
│     ↓                                                                   │
│  2. Validate PipelineConfig                                             │
│     - target_repo exists?                                               │
│     - worktree_root writable?                                           │
│     - skills_source readable?                                           │
│     ↓                                                                   │
│  3. Parse Spec → Extract Tasks                                          │
│     ↓                                                                   │
│  4. For each Task:                                                      │
│     ├── 4a. Resolve Skills (SkillResolver)                             │
│     │       - Match task description to triggers                        │
│     │       - Load matching skill definitions                           │
│     │                                                                   │
│     ├── 4b. Gather Context (KnowledgeAggregator)                       │
│     │       - Load API reference for skill.context_required             │
│     │       - Load domain models for skill.context_required             │
│     │       - Load patterns for skill.context_required                  │
│     │                                                                   │
│     ├── 4c. Create Worktree (MultiRepoExecutor)                        │
│     │       - git worktree add in target_repo                           │
│     │       - Create feature branch                                     │
│     │                                                                   │
│     ├── 4d. Execute Task                                               │
│     │       - Agent receives: skill + context + task                    │
│     │       - Agent generates code in worktree                          │
│     │       - Agent follows skill.instructions                          │
│     │                                                                   │
│     ├── 4e. Validate Outputs                                           │
│     │       - Run skill.validation checks                               │
│     │       - TypeScript compiles?                                      │
│     │       - ESLint passes?                                            │
│     │       - Expected files created?                                   │
│     │                                                                   │
│     └── 4f. Commit Changes                                             │
│             - Commit to feature branch                                  │
│             - Record in task result                                     │
│     ↓                                                                   │
│  5. Merge Branches → Create PR                                          │
│     ↓                                                                   │
│  6. Return Pipeline Result                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Config & Validation (Week 1)

1. Create PipelineConfig model with required fields
2. Create ConfigValidator service
3. Add /validate-config endpoint
4. Update pipeline execution to require config

### Phase 2: Skill Resolution (Week 2)

1. Create SkillDefinition model
2. Create SkillResolver service
3. Add /skills/* endpoints
4. Integrate with task execution

### Phase 3: Knowledge Aggregation (Week 3)

1. Create AgentContext model
2. Create KnowledgeAggregator service
3. Add /knowledge/* endpoints
4. Integrate with agent execution

### Phase 4: Multi-Repo Execution (Week 4)

1. Create MultiRepoExecutor service
2. Update worktree management for external repos
3. Add validation after execution
4. Test with CommandCentral frontend build

---

## Migration Path

### From CC4 Pipeline

Current CC4 pipeline execution (in `CC4/app/services/`):
- `spec_extractor.py`
- `task_orchestrator.py`
- `agent_runner.py`
- `worktree_manager.py`

Migration steps:
1. Copy base execution logic to PIPELZR
2. Add skill resolution layer
3. Add knowledge aggregation layer
4. Update to use PipelineConfig
5. Test with CommandCentral
6. Deprecate CC4 pipeline for cross-repo work

### Backward Compatibility

- CC4 internal work can continue using existing pipeline
- New cross-repo work must use PIPELZR with config
- Eventually migrate all execution to PIPELZR

---

## Success Criteria

1. **Config Validation**
   - [ ] Pipeline execution fails fast if config invalid
   - [ ] Clear error messages for missing fields

2. **Skill Resolution**
   - [ ] Tasks match to correct skills
   - [ ] Multiple skills can be combined
   - [ ] Unknown tasks get generic handling

3. **Knowledge Aggregation**
   - [ ] Agents receive relevant API docs
   - [ ] Agents receive relevant model docs
   - [ ] Context is scoped to task needs

4. **Multi-Repo Execution**
   - [ ] Code generated in target repo, not CC4
   - [ ] Worktrees isolated per task
   - [ ] Validation runs in target context

5. **CommandCentral Frontend**
   - [ ] Successfully build with new system
   - [ ] Generated code matches spec
   - [ ] All validation checks pass

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Skill matching too broad | Wrong code generated | Weight triggers, require high match score |
| Knowledge context too large | Token limits | Load only required sections |
| Worktree conflicts | Failed execution | Unique worktree per task |
| External repo access issues | Pipeline failure | Validate upfront, clear errors |

---

## Dependencies

- CommandCentral self-documentation (created)
- Skill definition standard (created)
- Pipeline config standard (created)
- PIPELZR backend restructure (needed)

---

## Next Steps

1. Review and approve this plan
2. Create PIPELZR feature branch
3. Implement Phase 1 (Config & Validation)
4. Test with simple pipeline
5. Proceed to Phase 2
