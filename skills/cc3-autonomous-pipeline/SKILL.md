---
status: active
name: cc3-autonomous-pipeline
description: 'Operational knowledge for CommandCenter V3 autonomous execution pipeline.
  Use when running autonomous batch execution, debugging pipeline failures, or understanding
  CC3 architecture. Critical rules: never use --reload, local mode runs sequentially,
  PATH needs /opt/homebrew/bin.'
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
# CC3 Autonomous Pipeline Operations

## Critical Rules

### 1. NEVER use `--reload`

```bash
# CORRECT
uvicorn app.main:app --port 8001

# WRONG - kills background tasks
uvicorn app.main:app --port 8001 --reload
```

**Why:** File changes trigger restart, killing execution mid-task.

### 2. Local mode = Sequential

Local mode forces `max_concurrent=1` to prevent git race conditions.

For parallel execution, use dagger mode:
```json
{"execution_mode": "dagger"}
```

### 3. PATH Configuration

Claude CLI requires `/opt/homebrew/bin` in PATH. Already fixed in:
- `agent_service.py` line 338 (local mode)
- `agent_service.py` line 603 (dagger mode)

### 4. No Manual Intervention

Don't commit/revert during execution. Pollutes git state for remaining tasks.

---

## Quick Start

```bash
cd ~/Projects/CommandCenterV3/backend
source .venv/bin/activate
uvicorn app.main:app --port 8001

curl -X POST http://localhost:8001/api/v1/autonomous/start \
  -H "Content-Type: application/json" \
  -d '{
    "plan_path": "/Users/danielconnolly/Projects/CommandCenterV3/docs/plans/MASTER_PLAN.md",
    "start_batch": 31,
    "end_batch": 37,
    "execution_mode": "local"
  }'
```

---

## Execution Modes

| Mode | Parallelism | Use Case |
|------|-------------|----------|
| `local` | Sequential | Debug, small batches |
| `dagger` | 4 concurrent | Production, large batches |

---

## Common Failures

### "Claude CLI not found"
Already fixed. Verify: `which claude` → `/opt/homebrew/bin/claude`

### "No commits between branches"
Causes: Manual intervention, git race (fixed), no files created.
Fix: Delete branch, rerun.

### Tasks stuck in "executing"
Causes: --reload restart, process killed, timeout.
Fix: Mark session failed in DB.

### Greenlet errors
Cause: Async DB in background tasks.
Fix: Use `get_sync_db()` not `get_db()`.

---

## Monitoring

```bash
# Watch logs
tail -f ~/Projects/CommandCenterV3/backend/logs/app.log

# Check status
curl -s http://localhost:8001/api/v1/autonomous/{id}/status | python3 -m json.tool
```

```python
# Database queries
from app.database import get_sync_db
from app.models.autonomous import AutonomousSession
from sqlalchemy import select

with get_sync_db() as db:
    result = db.execute(
        select(AutonomousSession).order_by(AutonomousSession.started_at.desc()).limit(5)
    )
    for s in result.scalars():
        print(f"{s.id}: {s.status} - {s.tasks_completed}/{s.tasks_total}")
```

---

## Architecture

```
Plan Parser → Batch Orchestrator → Execution Runner
                                         ↓
Merge Manager ← PR Reviewer ← Task Executor → Agent Service (Claude CLI)
```

### Key Files
- `services/agent_service.py` - Claude CLI execution
- `services/task_executor.py` - Sequential local execution
- `services/execution_runner.py` - Sync DB operations
- `docs/reference/runbook-01-11-21:08.md` - Full operational documentation

---

## Branch Cleanup

```bash
# Local
git branch | grep -E 'feature/|agent/' | xargs git branch -D

# Remote
git branch -r | grep -v main | sed 's/origin\///' | xargs -I {} git push origin --delete {}
git fetch --prune
```

---

## Lessons Learned

1. **subprocess ignores shell PATH** - Must add `/opt/homebrew/bin` explicitly
2. **--reload + background tasks = disaster** - Server restart kills execution
3. **Parallel git checkout = race condition** - Sequential only in local mode
4. **Async DB in background = greenlet error** - Use sync DB context
5. **Git commits = source of truth** - No separate status files
