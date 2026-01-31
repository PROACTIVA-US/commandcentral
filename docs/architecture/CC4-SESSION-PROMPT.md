# CC4 Session Prompt: Resolve Microservices Skills Architecture

**Use this prompt to start a fresh session in CC4 to address the skills/knowledge distribution issue.**

---

## Context Handoff

Copy everything below this line into the new CC4 session:

---

# CRITICAL: Microservices Split - Skills & Knowledge Architecture

## Situation

We attempted to build a React frontend for CommandCentral (one of 4 microservices split from CC4) using CC4's pipeline system. The build failed because:

1. **Wrong Repository Context**: Pipeline executed in CC4 repo instead of CommandCentral repo
2. **Wrong Domain Knowledge**: Agents used CC4 patterns instead of CommandCentral patterns
3. **Context Bleed**: Agents marked tasks "complete" because similar CC4 code existed
4. **No Service Self-Knowledge**: CommandCentral has no skills or domain documentation

## The Fundamental Problem

CC4 is being split into 4 microservices:

| Service | Port | Responsibility |
|---------|------|----------------|
| CommandCentral | 8000 | Auth, projects, decisions, audit, entity state |
| PIPELZR | 8001 | Tasks, pipelines, agents, skills |
| VISLZR | 8002 | Canvas, nodes, relationships, exploration |
| IDEALZR | 8003 | Goals, hypotheses, evidence, forecasts, ideas |

**CC4 currently has all the "intelligence":**
- Spec extraction and task batching
- Agent orchestration
- Git worktree management
- Domain knowledge (implicit in codebase)
- Skills (implicit in agent prompts)

**The question: Where should this intelligence live in the split architecture?**

## Repository Locations

```
/Users/danielconnolly/Projects/CC4           # Monolith (current execution engine)
/Users/danielconnolly/Projects/CommandCentral # New microservice (needs frontend)
/Users/danielconnolly/Projects/pipelzr       # To be created or exists
/Users/danielconnolly/Projects/vislzr        # To be created or exists
/Users/danielconnolly/Projects/idealzr       # To be created or exists
```

## Detailed Documentation

Full analysis is at:
`/Users/danielconnolly/Projects/CommandCentral/docs/architecture/CRITICAL-microservices-split-issue.md`

This document contains:
- Why the frontend build failed (with specifics)
- 4 recommended solutions with implementation details
- Implementation roadmap (4 phases)
- Decision points that need resolution

## Your Tasks

### Task 1: Review and Decide

Read the critical issue document and make decisions on:

1. **Skill Ownership**:
   - Option A: Each service owns its skills
   - Option B: PIPELZR maintains central registry
   - Option C: Hybrid (each owns, PIPELZR indexes)

2. **Knowledge Format**:
   - Option A: Markdown files
   - Option B: JSON schemas
   - Option C: OpenAPI specs
   - Option D: Combination

3. **Execution Location**:
   - Option A: Continue from CC4 (short-term)
   - Option B: Migrate to PIPELZR now
   - Option C: Run from CommandCentral itself

4. **Shared Components**:
   - Option A: Shared UI library across all frontends
   - Option B: Independent implementations
   - Option C: Shared base (shadcn), independent apps

### Task 2: Create Service Self-Documentation Standard

Define how services describe themselves. Proposed structure:

```
/docs/self/
├── api-reference.md       # All endpoints
├── domain-model.md        # Entities and relationships
├── patterns.md            # Coding conventions
├── dependencies.md        # External deps
└── skills/
    └── manifest.json      # Available skills
```

Create this structure for CommandCentral first as the reference implementation.

### Task 3: Create Skill Definition Standard

Define how skills are specified. Proposed format:

```yaml
name: "skill-name"
version: "1.0.0"
domain: "commandcentral|pipelzr|vislzr|idealzr"
category: "frontend|backend|testing|deployment"

triggers:
  - pattern: "regex pattern that activates this skill"

context_required:
  - api_reference: "endpoints needed"
  - domain_model: ["entities needed"]
  - patterns: ["patterns to follow"]

outputs:
  - type: "component|hook|service|test"
    path: "relative/path/to/output"

validation:
  - check: "validation step"
```

### Task 4: Update Pipeline Configuration

Add explicit targeting to pipeline config:

```python
class PipelineConfig:
    target_repo: str       # REQUIRED: Full path to target repo
    target_branch: str     # Branch to work on
    worktree_root: str     # Where to create worktrees
    skills_source: str     # Where to fetch skills
    knowledge_source: str  # Where to fetch domain knowledge
    execution_context: dict  # Service name, port, tech stack
```

### Task 5: Create CommandCentral Self-Documentation

Based on the backend at `/Users/danielconnolly/Projects/CommandCentral/backend/`:

1. Document the API endpoints
2. Document the domain model (Project, Decision, AuditEntry, EntityState, User)
3. Document patterns used
4. Create initial skills for:
   - Auth UI (login, register, protected routes)
   - Project management UI
   - Decision/governance UI
   - Audit log UI

### Task 6: Plan PIPELZR Enhancement

Define what PIPELZR needs to become the central orchestrator:

1. Skill resolver endpoint
2. Knowledge aggregator endpoint
3. Multi-repo execution capability
4. Skill/knowledge caching

## Success Criteria

1. Clear decision on skill ownership and format
2. Service self-documentation standard defined
3. Skill manifest standard defined
4. CommandCentral has `/docs/self/` with complete documentation
5. At least 3 CommandCentral-specific skills defined
6. Pipeline can be configured to target CommandCentral repo explicitly

## Files to Reference

- `/Users/danielconnolly/Projects/CommandCentral/docs/architecture/CRITICAL-microservices-split-issue.md`
- `/Users/danielconnolly/Projects/CommandCentral/docs/architecture/skills-knowledge-distribution.md`
- `/Users/danielconnolly/Projects/CommandCentral/docs/specs/commandcentral-frontend.md`
- `/Users/danielconnolly/Projects/CommandCentral/backend/app/` (backend code to document)

## Constraints

- Do NOT attempt to build the frontend until the architecture is resolved
- Do NOT create branches in CC4 for CommandCentral work
- Do NOT modify CC4's existing frontend
- Focus on documentation and standards first
- Any code changes should be in CommandCentral or new directories in CC4

## Output Expected

1. Updated `CRITICAL-microservices-split-issue.md` with decisions made
2. New `/docs/standards/` directory with:
   - `service-self-documentation.md`
   - `skill-manifest-spec.md`
3. CommandCentral `/docs/self/` directory populated
4. At least one working skill definition as proof of concept
5. Updated pipeline configuration schema (can be proposal/spec)

---

**End of prompt. Start the CC4 session with this context.**
