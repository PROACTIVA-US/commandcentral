---
name: commandcenter-operations
description: How to properly operate CommandCenter - startup, agent execution, common pitfalls
priority: P0
enforcement: blocking
updated: 2026-01-11
---

# CommandCenter Operations

**READ THIS SKILL BEFORE ANY PIPELINE/AGENT WORK.**

## Critical Lessons Learned

### The Pipeline Hardening Incident (2026-01-09)

**What happened:** Hours were spent creating a 300-line "pipeline hardening" plan to fix problems that didn't exist or were already solved.

**Root cause:** Claude Code didn't read this skill or dagger-execution skill before starting work.

**The fix:** ALWAYS check skills BEFORE starting any task involving:
- Pipeline execution
- Agent service changes
- Dagger/container work
- Branch/merge operations

### The venv Corruption Scare (2026-01-11)

**What happened:** Investigation into "venv corruption" revealed the venv was healthy all along.

**Root cause:** Hypothesis without evidence. The "corruption" was documented as a concern, not actual evidence.

**The fix:** Verify issues exist before fixing them. Run diagnostics first:
```bash
# Check venv health
python -c "import sys; print(sys.executable)"
ls -la backend/.venv/bin/
pip list | wc -l  # Should show 100+ packages
```

## What is CommandCenter V3?

CommandCenter V3 is a **strategic intelligence and execution platform** that runs AI agents to build software. It is NOT just a FastAPI + React app - it's an **agent orchestration system**.

**V3 is the ACTIVE project.** Unlike earlier iterations where "CC2 builds CC3", V3 is self-contained.

## Startup Procedure

### Quick Start
```bash
cd ~/Projects/CommandCenterV3

# 1. Docker MUST be running (Dagger needs it)
open -a Docker

# 2. Backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --port 8001 --reload

# 3. Frontend (new terminal)
cd frontend && npm run dev

# 4. Verify
curl http://localhost:8001/health
open http://localhost:3001
```

### Pre-flight Checklist
```bash
# Is Docker running?
docker info > /dev/null && echo "✅ Docker OK" || echo "❌ Start Docker"

# Is backend healthy?
curl -s http://localhost:8001/health && echo "✅ Backend OK" || echo "❌ Start backend"

# Is frontend running?
curl -s -o /dev/null -w '%{http_code}' http://localhost:3001 && echo "✅ Frontend OK" || echo "❌ Start frontend"

# Are credentials valid? (for Dagger OAuth)
test -f ~/.claude-container/.credentials.json && echo "✅ Creds exist" || echo "⚠️ Export creds"
```

## Execution Modes

**ALWAYS use `dagger` mode for pipeline execution.**

| Mode | Cost | Parallel | Isolation | Use Case |
|------|------|----------|-----------|----------|
| **`dagger`** | FREE | ✅ | ✅ | **Pipeline execution** |
| `local` | FREE | ❌ | ❌ | Quick interactive tasks only |
| `e2b` | $$$$ | ✅ | ✅ | Cloud sandboxes (avoid) |

### Why Dagger?

```
Without Dagger:
  Agent 1 ──┐
  Agent 2 ──┼──> Same filesystem ──> CONFLICTS!
  Agent 3 ──┘

With Dagger:
  Agent 1 ──> Container 1 ──> Isolated ──> No conflicts
  Agent 2 ──> Container 2 ──> Isolated ──> Parallel OK
  Agent 3 ──> Container 3 ──> Isolated ──> FREE via OAuth
```

## Running the Autonomous Pipeline

### CORRECT: Use the autonomous API
```bash
# Start pipeline execution
curl -X POST http://localhost:8001/api/v1/autonomous/start \
  -H "Content-Type: application/json" \
  -d '{
    "plan_path": "docs/plans/CURRENT_PLAN.md",
    "execution_mode": "dagger"
  }'

# Check status
curl http://localhost:8001/api/v1/autonomous/{execution_id}/status
```

### WRONG: Don't bypass the pipeline
```bash
# DON'T DO THIS - bypasses safety, no PR review
curl -X POST http://localhost:8001/api/v1/ideas/execute \
  -d '{"input": "do something"}'
```

## Common Mistakes (AVOID THESE)

### 1. Not reading skills before work
**Symptom:** Hours wasted on problems already solved
**Fix:** `cat skills/MANIFEST.yaml` and read relevant P0 skills FIRST

### 2. Not starting Docker
**Symptom:** Agents run in "local" mode, no parallelism
**Fix:** `open -a Docker` before anything else

### 3. Wrong execution_mode
**Symptom:** No isolation, potential conflicts
**Fix:** Always specify `"execution_mode": "dagger"`

### 4. Fixing hypothetical problems
**Symptom:** Creating elaborate plans for issues that don't exist
**Fix:** Verify the problem exists with diagnostics BEFORE planning fixes

### 5. Context overloading
**Symptom:** Erratic context percentage (jumping 10% → 90% → 15%)
**Fix:** Check `~/.claude/mcp.json` for excessive MCP servers, disable unused plugins

## Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Entry point - points to skills |
| `AGENTS.md` | Coding standards |
| `skills/MANIFEST.yaml` | Skill index with keywords/patterns |
| `backend/app/services/agent_service.py` | Agent execution |
| `backend/app/services/task_executor.py` | Task → PR workflow |
| `backend/app/services/batch_orchestrator.py` | Pipeline batches |

## Architecture Reminders

### Pipeline Flow
```
Plan.md → Parser → Tasks → Executor → Agent → PR → Review → Merge
```

### Agent Service Modes
- `local`: Claude Code runs directly on host (USE SPARINGLY)
- `dagger`: Fresh clone in container, push from container (USE THIS)
- `e2b`: Cloud sandbox (EXPENSIVE)

### Safety Features in Dagger Mode
- Hardened sync validation (refuses if >20 deletions)
- Fresh clone from remote (no local state corruption)
- OAuth credential mounting (FREE with Claude Max)

## When Things Go Wrong

### Agent stuck or failing
1. Check execution status: `curl http://localhost:8001/api/v1/autonomous/{id}/status`
2. Check logs: `backend/logs/` or WebSocket events
3. Verify Docker is running
4. Check if PR was created (might be stuck in review)

### Context overloading
1. Run `/clear` in Claude Code
2. Check `~/.claude/mcp.json` for excessive servers
3. Disable heavy plugins
4. Start fresh session if needed

### Git conflicts
1. Use Dagger mode (clones fresh, doesn't touch local)
2. If local is dirty: `git stash` before pipeline
3. Check for orphan branches: `git branch -a`

---

## Summary

1. **READ SKILLS FIRST** - They contain hard-won knowledge
2. **USE DAGGER MODE** - FREE + Parallel + Isolated
3. **VERIFY BEFORE FIXING** - Diagnose before planning
4. **USE THE PIPELINE** - Don't bypass with raw API calls
5. **CHECK DOCKER** - Dagger needs it running
