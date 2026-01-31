---
title: CommandCentral Frontend Build - Handoff Document
created: 2026-01-31
status: ready
from_session: CC4 PIPELZR Enhancement
to_session: CommandCentral Frontend Build
---

# CommandCentral Frontend Build - Handoff Document

## Executive Summary

This document hands off from the CC4 PIPELZR enhancement session to a CommandCentral session that will build the frontend. **Use CC4's existing UX/UI pipeline** - it's ready and enhanced with skill resolution.

---

## What Was Built This Session

### 1. Skill Discovery Execution Logic
**File:** `/backend/app/services/skill_resolver.py`

Resolves skills for tasks using:
- Trigger pattern matching (regex/keywords)
- Semantic search via KnowledgeBeast
- Keyword matching
- Hybrid scoring

```python
from app.services.skill_resolver import SkillResolver, get_skill_resolver

resolver = get_skill_resolver(db)
result = await resolver.resolve(
    task_description="Build login page with OAuth",
    target_service="commandcentral",
    context={"tech_stack": ["react", "typescript"]}
)
```

### 2. Pipeline Failure Policies
**Enum:** `FailurePolicy` in `skill_resolver.py`

| Policy | Behavior |
|--------|----------|
| `RETRY_SAME` | Retry same skill up to 3 times |
| `TRY_ALTERNATIVE` | Try next best matching skill |
| `FALLBACK_GENERIC` | Use generic approach |
| `ESCALATE_HUMAN` | Require human intervention |
| `ABORT` | Stop execution |

### 3. Skill Versioning Protocol
**File:** `/backend/app/services/skill_versioning.py`

- Semantic versioning (major.minor.patch)
- Compatibility checking
- Effectiveness tracking per version
- Breaking change detection

### 4. Observability Layer
**File:** `/backend/app/services/skill_observability.py`

- Structured logging with correlation IDs
- Prometheus-compatible metrics
- Event history with filtering
- Health checks and diagnostics

### 5. API Endpoints
**Router:** `/api/v1/skills/resolve` (17 endpoints)

Key endpoints:
```bash
# Resolve skills for a task
POST http://localhost:8001/api/v1/skills/resolve
{
  "task_description": "Build login page",
  "target_service": "commandcentral",
  "limit": 5
}

# Batch resolve for pipeline
POST http://localhost:8001/api/v1/skills/resolve/batch
{
  "tasks": [
    {"id": "1", "description": "Create auth store"},
    {"id": "2", "description": "Build login form"}
  ],
  "target_service": "commandcentral"
}

# Get metrics
GET http://localhost:8001/api/v1/skills/resolve/metrics

# Get observability health
GET http://localhost:8001/api/v1/skills/resolve/observability/health
```

---

## How to Build CommandCentral Frontend

### Option A: Use CC4's Existing UX Pipeline (Recommended)

CC4 already has a working UX/UI validation pipeline. Use it directly:

1. **Start CC4 backend** (if not running):
   ```bash
   cd ~/Projects/CC4/backend
   source .venv/bin/activate
   uvicorn app.main:app --reload --port 8001
   ```

2. **Create spec in CommandCentral**:
   ```
   ~/Projects/CommandCentral/docs/specs/frontend-spec.md
   ```

3. **Configure pipeline to target CommandCentral**:
   ```json
   {
     "spec_path": "/Users/danielconnolly/Projects/CommandCentral/docs/specs/frontend-spec.md",
     "target_repo": "file:///Users/danielconnolly/Projects/CommandCentral",
     "worktree_root": "/tmp/commandcentral-worktrees",
     "skills_source": "local:///Users/danielconnolly/Projects/CommandCentral/docs/self/skills",
     "knowledge_source": "local:///Users/danielconnolly/Projects/CommandCentral/docs/self"
   }
   ```

4. **Run pipeline via API or CLI**

### Option B: Manual Build with Skill Injection

Build manually but use skill resolution for guidance:

1. **Query skills before each task**:
   ```bash
   curl -X POST http://localhost:8001/api/v1/skills/resolve \
     -H "Content-Type: application/json" \
     -d '{"task_description": "Build dashboard layout with sidebar"}'
   ```

2. **Use returned skills as context** for Claude Code prompts

3. **Record feedback** after completion:
   ```bash
   curl -X POST http://localhost:8001/api/v1/skills/resolve/feedback \
     -H "Content-Type: application/json" \
     -d '{"skill_id": "dashboard-layout", "success": true}'
   ```

---

## What CommandCentral Needs First

Before building the frontend, create self-documentation in CommandCentral:

### 1. API Reference
**File:** `CommandCentral/docs/self/api-reference.md`

Document all endpoints:
- `/api/v1/auth/*` - Login, register, logout, me
- `/api/v1/projects/*` - CRUD, members, settings
- `/api/v1/decisions/*` - CRUD, state transitions
- `/api/v1/audit/*` - Query, export
- `/api/v1/events/*` - Stream, history

### 2. Domain Model
**File:** `CommandCentral/docs/self/domain-model.md`

```yaml
entities:
  Project: "Container for all work, has settings and members"
  Decision: "Governance item with state machine lifecycle"
  AuditEntry: "Immutable log of all state changes"
  EntityState: "Tracks lifecycle state of any entity"
  User: "Authentication identity with roles"
```

### 3. Frontend Skills
**Directory:** `CommandCentral/docs/self/skills/`

Create skills for:
- `auth-pages.md` - Login, register, logout UI
- `dashboard.md` - Cross-service dashboard
- `governance.md` - Decisions and audit UI
- `project-management.md` - Project CRUD UI

### 4. Patterns
**File:** `CommandCentral/docs/self/patterns.md`

Document:
- Component structure (shadcn, Zustand stores)
- API integration patterns
- State management approach
- Routing structure

---

## Arena Review Consensus (From This Session)

The AI Arena reviewed the architecture with Claude Opus 4.5, GPT-5.2, and Grok-3:

1. **PIPELZR should be Skill Contract Registry** (not just index) ✅ Implemented
2. **Knowledge Radar as standalone package** (Option B) - Future work
3. **Skills indexed in KnowledgeBeast** ✅ 48 skills indexed

### Next Steps from Arena:
1. ✅ Implement skill-discovery execution logic
2. ✅ Define pipeline failure policies
3. ✅ Create skill versioning protocol
4. ✅ Build observability layer
5. ⏳ Create CommandCentral self-documentation
6. ⏳ Build CommandCentral frontend

---

## Files Created This Session

| File | Purpose |
|------|---------|
| `backend/app/services/skill_resolver.py` | Task-to-skill matching with multiple strategies |
| `backend/app/services/skill_versioning.py` | Version management and compatibility |
| `backend/app/services/skill_observability.py` | Metrics, events, health checks |
| `backend/app/routers/skill_resolution.py` | API endpoints (17 total) |

### Modified Files

| File | Change |
|------|--------|
| `backend/app/main.py` | Added skill_resolution_router import and registration |

---

## Quick Start for CommandCentral Session

```bash
# 1. Start CC4 backend (for skill resolution)
cd ~/Projects/CC4/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001

# 2. In new terminal, go to CommandCentral
cd ~/Projects/CommandCentral

# 3. Create self-documentation structure
mkdir -p docs/self/skills

# 4. Query KB for existing patterns
curl -X POST http://localhost:8001/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "frontend patterns react typescript"}'

# 5. Start building!
```

---

## Key Decisions Made

1. **Use CC4 pipeline now** - Don't wait for full PIPELZR split
2. **Skills live in target service** - CommandCentral owns its skills, CC4 indexes them
3. **Semantic + keyword matching** - Hybrid approach for best results
4. **Failure policies are automatic** - Based on match confidence

---

## Contact Points

- **CC4 Backend:** http://localhost:8001
- **Skill Resolution API:** http://localhost:8001/api/v1/skills/resolve
- **KnowledgeBeast:** http://localhost:8001/api/v1/knowledge/search
- **Arena (model testing):** http://localhost:8001/api/v1/arena/preflight

---

*Generated: 2026-01-31*
*Session: CC4 PIPELZR Enhancement*
