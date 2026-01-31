# CRITICAL: Microservices Split - Skills & Knowledge Architecture

**Priority:** BLOCKING
**Date:** 2026-01-31
**Status:** Requires architectural decision before proceeding

---

## Executive Summary

Splitting CC4 into 4 microservices (CommandCentral, PIPELZR, VISLZR, IDEALZR) has exposed a fundamental architectural gap: **the skills and knowledge required for autonomous development work have no defined home in the split architecture**.

CC4's pipeline system successfully orchestrates complex multi-task development work by leveraging:
- Domain-specific skills (how to build features)
- Codebase knowledge (patterns, conventions, dependencies)
- Execution context (repo structure, tooling, workflows)

When we attempted to build CommandCentral's frontend using CC4's pipeline, **the agents operated in CC4's context instead of CommandCentral's context**, producing incorrect or incomplete work.

---

## The Problem in Detail

### What CC4 Currently Has

CC4 is a monolith with integrated intelligence:

```
CC4 (Monolith)
├── /app/                      # Backend (FastAPI)
│   ├── /models/               # All domain models
│   ├── /routers/              # All API endpoints
│   └── /services/             # Business logic + Pipeline execution
├── /frontend/                 # React frontend
│   ├── /src/stores/           # 23 Zustand stores
│   ├── /src/components/       # UI components
│   └── /src/pages/            # Page components
├── /skills/                   # Agent skills (implicit in prompts)
├── /specs/                    # Specification documents
└── Pipeline Intelligence:
    ├── Spec extraction
    ├── Task dependency analysis
    ├── Git worktree management
    ├── Agent orchestration
    ├── Failure recovery
    └── PR automation
```

### What the Split Looks Like

After splitting, we have:

```
CommandCentral (port 8000)     PIPELZR (port 8001)
├── /backend/                  ├── /backend/
│   ├── Auth                   │   ├── Tasks
│   ├── Projects               │   ├── Pipelines
│   ├── Decisions              │   ├── Agents
│   └── Audit                  │   └── Skills
└── /frontend/ (TO BUILD)      └── /frontend/ (TO BUILD)

VISLZR (port 8002)             IDEALZR (port 8003)
├── /backend/                  ├── /backend/
│   ├── Canvas                 │   ├── Goals
│   ├── Nodes                  │   ├── Hypotheses
│   └── Relationships          │   ├── Evidence
└── /frontend/ (TO BUILD)      │   └── Forecasts
                               └── /frontend/ (TO BUILD)
```

### The Gap

**Where does the pipeline intelligence go?**

| Capability | Current Location | Should Live In |
|------------|-----------------|----------------|
| Spec extraction | CC4/app/services | PIPELZR? |
| Task orchestration | CC4/app/services | PIPELZR? |
| Git worktree management | CC4/app/services | PIPELZR? |
| Agent execution | CC4/app/services | PIPELZR? |
| Domain skills | Implicit in CC4 | Each service? |
| Codebase knowledge | Implicit in CC4 | Each service? |
| Failure recovery | CC4/app/services | PIPELZR? |

**Where does domain knowledge go?**

| Knowledge Type | Current State | Required State |
|---------------|---------------|----------------|
| CommandCentral domain | N/A (new service) | CommandCentral must describe itself |
| PIPELZR domain | In CC4's pipeline code | PIPELZR must describe itself |
| VISLZR domain | In CC4's canvas code | VISLZR must describe itself |
| IDEALZR domain | In CC4's strategic code | IDEALZR must describe itself |
| Cross-service patterns | N/A | Shared library or registry |

---

## Why the Frontend Build Failed

### Attempted Workflow
1. Created spec document at `CommandCentral/docs/specs/commandcentral-frontend.md`
2. Triggered CC4's pipeline system to execute the spec
3. Pipeline created branches in CC4 repo
4. Agents started executing tasks

### What Went Wrong

**Problem 1: Wrong Repository Context**
- Pipeline was configured for CC4, not CommandCentral
- Agents created code in CC4's existing frontend directory
- CC4's frontend already has 23 stores, different routing, different architecture

**Problem 2: Wrong Domain Knowledge**
- Agents knew CC4's patterns (Canvas/Pipelines/Intel tabs)
- Agents didn't know CommandCentral patterns (Dashboard/IDEALZR/PIPELZR/VISLZR/Governance tabs)
- Generated code followed CC4 conventions, not the spec

**Problem 3: Context Bleed**
- Task 4 (Zustand stores): Marked complete because CC4 already has stores
- Task 6 (React Router): Marked complete because CC4 already has routing
- Task 5 (Layout components): Agent timed out trying to reconcile spec vs reality

**Problem 4: No Service Self-Knowledge**
- CommandCentral has no `/skills` or `/knowledge` directories
- No description of CommandCentral's API structure for agents to reference
- No definition of CommandCentral's domain model

---

## Recommended Solutions

### Solution 1: Service Self-Documentation (Required)

Each microservice needs a `/docs/self` directory that describes:

```
/docs/self/
├── api-reference.md       # All endpoints, request/response schemas
├── domain-model.md        # Core entities and their relationships
├── patterns.md            # Coding conventions, patterns used
├── dependencies.md        # External dependencies and versions
└── skills-manifest.json   # Skills available for this service
```

**For CommandCentral:**
```yaml
# /docs/self/domain-model.md
entities:
  - Project: "Container for all work, has settings and members"
  - Decision: "Governance item with state machine lifecycle"
  - AuditEntry: "Immutable log of all state changes"
  - EntityState: "Tracks lifecycle state of any entity"
  - User: "Authentication identity with roles"

api_structure:
  auth: /api/v1/auth/* (login, register, me, logout)
  projects: /api/v1/projects/* (CRUD, members, settings)
  decisions: /api/v1/decisions/* (CRUD, state transitions)
  audit: /api/v1/audit/* (query, export)
  events: /api/v1/events/* (stream, history)
```

### Solution 2: PIPELZR as Orchestrator (Recommended)

PIPELZR should own the execution engine and skill resolution:

```
PIPELZR
├── /backend/
│   ├── /services/
│   │   ├── spec_extractor.py      # Parse specs into tasks
│   │   ├── task_orchestrator.py   # Manage execution order
│   │   ├── agent_runner.py        # Execute tasks via Claude
│   │   ├── worktree_manager.py    # Git isolation
│   │   ├── skill_resolver.py      # Fetch skills from services
│   │   └── knowledge_aggregator.py # Gather context
│   └── /api/
│       ├── /pipeline/             # Pipeline CRUD & execution
│       └── /skills/               # Skill registry & resolution
├── /core-skills/                  # Shared skills (git, testing, npm)
└── /docs/
    └── skill-specification.md     # How to define skills
```

**Skill Resolution Flow:**
```
1. PIPELZR receives task: "Build CommandCentral login page"
2. PIPELZR queries CommandCentral: GET /api/v1/skills?domain=auth
3. CommandCentral returns skill: "auth-page-skill"
4. PIPELZR queries CommandCentral: GET /api/v1/knowledge?topic=auth
5. CommandCentral returns context: API schemas, patterns, dependencies
6. PIPELZR executes task with skill + knowledge
7. Agent generates code in CommandCentral repo
```

### Solution 3: Skill Definition Standard

Define a standard for how skills are described:

```yaml
# skill-manifest.yaml
name: "commandcentral-frontend-auth"
version: "1.0.0"
domain: "commandcentral"
category: "frontend"

triggers:
  - pattern: "login page|login form|authentication UI"
  - pattern: "register page|signup form"
  - pattern: "protected route|auth guard"

context_required:
  - api_reference: "/api/v1/auth/*"
  - domain_model: ["User", "Token", "Session"]
  - patterns: ["react-hook-form", "zod-validation", "shadcn-ui"]

outputs:
  - type: "component"
    path: "src/pages/LoginPage.tsx"
  - type: "component"
    path: "src/components/auth/LoginForm.tsx"
  - type: "hook"
    path: "src/hooks/useAuth.ts"

examples:
  - input: "Create login page with email/password"
    reference: "examples/login-page.tsx"

validation:
  - check: "typescript_compiles"
  - check: "no_eslint_errors"
  - check: "renders_without_crash"
```

### Solution 4: Repository Targeting

The pipeline must explicitly target the correct repository:

```python
# pipeline_config.py
class PipelineConfig:
    target_repo: str  # MUST be explicit: "file:///path/to/CommandCentral"
    target_branch: str = "main"
    worktree_root: str  # Separate from CC4's worktrees
    skills_source: str  # Where to fetch skills from
    knowledge_source: str  # Where to fetch domain knowledge
```

**Configuration for CommandCentral frontend build:**
```json
{
  "spec_path": "/Users/danielconnolly/Projects/CommandCentral/docs/specs/commandcentral-frontend.md",
  "target_repo": "file:///Users/danielconnolly/Projects/CommandCentral",
  "target_branch": "main",
  "worktree_root": "/tmp/commandcentral-worktrees",
  "skills_source": "local:///Users/danielconnolly/Projects/CommandCentral/docs/self/skills",
  "knowledge_source": "local:///Users/danielconnolly/Projects/CommandCentral/docs/self",
  "execution_context": {
    "service": "commandcentral",
    "port": 8000,
    "tech_stack": ["react", "typescript", "tailwind", "shadcn", "zustand"]
  }
}
```

---

## Implementation Roadmap

### Phase 1: Foundation (Do First)

1. **Create self-documentation for CommandCentral**
   - `/docs/self/api-reference.md`
   - `/docs/self/domain-model.md`
   - `/docs/self/patterns.md`

2. **Define skill manifest standard**
   - Create `/docs/standards/skill-manifest-spec.md`
   - Define JSON schema for skills

3. **Create CommandCentral-specific skills**
   - `auth-page-skill`: Login, register, logout UI
   - `dashboard-skill`: Cross-service dashboard
   - `governance-skill`: Decisions, audit UI

### Phase 2: PIPELZR Enhancement

4. **Add skill resolver to PIPELZR**
   - Endpoint: `GET /api/v1/skills/resolve?domain=X&task=Y`
   - Fetches from skill registry or service endpoints

5. **Add knowledge aggregator to PIPELZR**
   - Endpoint: `GET /api/v1/knowledge/context?service=X&topic=Y`
   - Combines service self-docs with shared patterns

6. **Update pipeline config**
   - Add `target_repo` as required field
   - Add `skills_source` and `knowledge_source`
   - Validate repo exists before execution

### Phase 3: Re-attempt Frontend Build

7. **Run CommandCentral frontend build**
   - With proper config targeting CommandCentral repo
   - With CommandCentral-specific skills
   - With CommandCentral domain knowledge

8. **Validate and iterate**
   - Check generated code matches spec
   - Refine skills based on results
   - Document learnings

### Phase 4: Replicate for Other Services

9. **Create self-documentation for PIPELZR, VISLZR, IDEALZR**
10. **Create service-specific skills for each**
11. **Build remaining frontends**

---

## Decision Points Needed

Before proceeding, decisions are needed on:

1. **Skill Ownership**
   - Does each service own its skills?
   - Or does PIPELZR maintain a central registry?
   - Recommendation: Each service owns, PIPELZR indexes

2. **Knowledge Format**
   - Markdown files? JSON schemas? OpenAPI specs?
   - Recommendation: Markdown for human-readable, JSON schema for machines

3. **Execution Location**
   - Continue running from CC4?
   - Migrate execution to PIPELZR?
   - Recommendation: CC4 short-term, PIPELZR long-term

4. **Shared Components**
   - Should all 4 frontends share a UI library?
   - Or be completely independent?
   - Recommendation: Shared base (shadcn), independent implementations

---

## Files Changed

**Deleted Branches (CC4):**
- `batch-1/commandcentral-frontend-20260131-175755`
- `batch-2/commandcentral-frontend-20260131-175755`
- `feature/commandcentral-frontend-20260131-175755`
- `task/batch-1-commandcentral-frontend-20260131-175755/task-002`
- `task/batch-1-commandcentral-frontend-20260131-175755/task-003`
- `task/batch-2-commandcentral-frontend-20260131-175755/task-004`
- `task/batch-2-commandcentral-frontend-20260131-175755/task-005`
- `task/batch-2-commandcentral-frontend-20260131-175755/task-006`

**Recovery Files:**
- `/tmp/cc2_recovery/exec_627bee32/attempt_history.json`

---

## Next Steps

1. Review this document and make decisions on the decision points
2. Start a fresh CC4 session with proper context (see accompanying prompt)
3. Create CommandCentral self-documentation
4. Re-attempt frontend build with correct configuration
