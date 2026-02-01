---
status: active
name: operations
description: How to run CommandCenter V3 - startup, execution modes, pipeline usage.
  CRITICAL rules for autonomous execution.
priority: P0
updated: 2026-01-12
contract:
  version: '1.0'
  inputs:
    required:
    - name: task_description
      type: string
      description: Description of the task to perform
    optional: []
  outputs:
  - name: result
    type: object
    properties:
      success:
        type: boolean
      summary:
        type: string
  errors:
  - code: SKILL_EXECUTION_FAILED
    description: Skill execution encountered an error
    recoverable: true
  side_effects:
  - type: file_write
    description: May modify files
  - type: git_commit
    description: May create git commits
  - type: api_call
    description: May call external APIs
  - type: database_write
    description: May modify database
  auth_scopes:
  - scope: file:write
    required: true
  - scope: git:commit
    required: false
  timeouts:
    default_ms: 30000
    max_ms: 180000
---
# CommandCenter Operations

**READ THIS BEFORE ANY PIPELINE/AGENT/EXECUTION WORK.**

## Critical Rules (Phase 2 Lessons)

### ⚠️ NEVER use `--reload` for autonomous execution
```bash
# AUTONOMOUS MODE - correct
uvicorn app.main:app --port 8001

# DEVELOPMENT ONLY - will kill background tasks
uvicorn app.main:app --port 8001 --reload
```
**Why:** File changes restart server, killing tasks mid-execution.

### ⚠️ Local mode = Sequential (by design)
`max_concurrent` is forced to 1 in local mode to prevent git race conditions.

**For parallel execution:** Use `"execution_mode": "dagger"`

### ⚠️ Don't manually intervene during execution
Let pipeline complete or fail. Manual commits corrupt git state for remaining tasks.

---

## Essence (50 words)

Docker first. Dagger for pipeline (parallel + isolated). Local for quick tests only. NEVER --reload for autonomous. Pipeline clones fresh, pushes from container. Your local repo stays clean. Credentials at `~/.claude-container/`. Check skills before major work.

---

## Quick Start

### Development (with reload)
```bash
cd ~/Projects/CommandCenterV3/backend
source .venv/bin/activate
uvicorn app.main:app --port 8001 --reload  # OK for dev
```

### Autonomous Execution (NO reload)
```bash
cd ~/Projects/CommandCenterV3/backend
source .venv/bin/activate
uvicorn app.main:app --port 8001  # NO --reload!

# Run a phase
curl -X POST http://localhost:8001/api/v1/autonomous/start \
  -H "Content-Type: application/json" \
  -d '{
    "plan_path": "/path/to/MASTER_PLAN.md",
    "start_batch": 31,
    "end_batch": 37,
    "execution_mode": "local"
  }'
```

## Execution Modes

| Mode | Parallelism | Isolation | Use Case |
|------|-------------|-----------|----------|
| `dagger` | Parallel (4x) | Full (containers) | **Production, large batches** |
| `local` | Sequential | None | Development, debugging |

### Why Local is Sequential
Multiple tasks doing `git checkout` on same repo = race condition. Fixed in `task_executor.py` line 839.

## Pre-flight Check

```bash
docker info > /dev/null && echo "✅ Docker" || echo "❌ Start Docker"
curl -s http://localhost:8001/health && echo "✅ Backend" || echo "❌ Start backend"
test -f ~/.claude-container/.credentials.json && echo "✅ Creds" || echo "❌ Export creds"
which claude && echo "✅ Claude CLI" || echo "❌ Install claude"
```

## OAuth Credentials

```bash
# Export from macOS Keychain (one-time)
./scripts/export-claude-credentials.sh

# Manual if needed
mkdir -p ~/.claude-container
security find-generic-password -s "Claude Code-credentials" -w > ~/.claude-container/.credentials.json
```

## Key Files

| File | Purpose | Critical Lines |
|------|---------|----------------|
| `services/agent_service.py` | Agent execution | 338-339 (PATH fix) |
| `services/task_executor.py` | Task lifecycle | 839 (sequential fix) |
| `services/execution_runner.py` | Batch execution | Uses sync DB |
| `services/batch_orchestrator.py` | Pipeline batches | |

## Common Failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Claude CLI not found" | PATH missing homebrew | Fixed in agent_service.py |
| Tasks stuck "executing" | --reload killed them | Restart WITHOUT --reload |
| "No commits between branches" | Race condition or manual intervention | Sequential mode (fixed) |
| Greenlet error | Async DB in background | Use get_sync_db() |

See `skills/lessons/SKILL.md` for detailed incidents.

---

*Docker first. Dagger for production. NO --reload for autonomous.*
