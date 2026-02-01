---
name: dagger-execution
description: Run parallel Claude Code agents in isolated Dagger containers with FREE OAuth authentication
updated: 2026-01-11
---

# Dagger Execution

Run parallel, isolated Claude Code agents using Dagger containers. Provides **FREE** parallel execution using Claude Max OAuth credentials.

## ✅ STATUS: PRODUCTION READY

As of 2026-01-11, Dagger execution mode is fully operational with:
- OAuth authentication (FREE via Claude Max)
- Pipeline isolation (clone from remote, push from container)
- ~8 second execution time for simple tasks
- No local repo modification during pipeline runs

## When to Use

- **Parallel development**: Multiple features simultaneously without git conflicts
- **Fast iteration**: ~8s total execution for simple tasks
- **Offline work**: Works without internet after initial image pull
- **FREE execution**: Uses Claude Max subscription (no API costs!)
- **Pipeline execution**: Safe parallel agent orchestration

## Two Execution Modes

### Pipeline Mode (branch specified)
Used for autonomous pipeline execution. Completely isolated from your local repo.

```python
# Triggered when branch parameter is provided
session = await service.run(
    task="Your task",
    execution_mode="dagger",
    branch="feature/my-task"  # ← Pipeline mode
)
```

**Flow:**
1. Clone fresh from remote into container
2. Create/checkout branch
3. Run Claude Code
4. Commit changes inside container
5. Push directly from container to GitHub
6. Container discarded - **no sync to host**

**Benefits:**
- Local repo unchanged (you can keep working!)
- Multiple agents can run in parallel on different branches
- No merge conflicts with local work
- Git history is clean

### Testing Mode (no branch)
Used for local testing and iteration. Syncs changes back to your local repo.

```python
# Triggered when branch is NOT specified
session = await service.run(
    task="Your task",
    execution_mode="dagger"
    # No branch = testing mode
)
```

**Flow:**
1. Mount local repo into container
2. Run Claude Code
3. Validate changes (refuse if >20 deletions)
4. Sync changes back to host
5. Files modified locally

**Use for:** Quick tests, single changes, development iteration

## Prerequisites

1. **Docker Desktop** must be running
2. **Dagger SDK**: `pip install dagger-io`
3. **Claude credentials exported** (see below)

## OAuth Authentication Setup

Claude Max OAuth credentials CAN be used in containers. The key insight: credentials are injected via Dagger secrets, not mounted directories.

### Export Credentials (One-time setup)

```bash
# Run this before using Dagger mode
./scripts/export-claude-credentials.sh
```

This script:
1. Extracts OAuth tokens from macOS Keychain
2. Writes them to `~/.claude-container/.credentials.json`
3. Credentials are valid for ~1 year

### Manual Export

```bash
# Create directory
mkdir -p ~/.claude-container

# Extract from Keychain
security find-generic-password -s "Claude Code-credentials" -w > ~/.claude-container/.credentials.json

# Verify
cat ~/.claude-container/.credentials.json | jq '.claudeAiOauth.scopes'
# Should output: ["user:inference"]
```

## API Usage

### Single Agent (Pipeline Mode)

```bash
curl -X POST http://localhost:8001/api/v1/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Your task description",
    "execution_mode": "dagger",
    "model": "sonnet",
    "branch": "feature/my-task"
  }'
```

### Single Agent (Testing Mode)

```bash
curl -X POST http://localhost:8001/api/v1/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Your task description",
    "execution_mode": "dagger",
    "model": "sonnet"
  }'
```

### Parallel Agents (Pipeline Mode)

```bash
curl -X POST http://localhost:8001/api/v1/agents/run-parallel \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"task": "Task 1", "branch": "feature/task-1"},
      {"task": "Task 2", "branch": "feature/task-2"},
      {"task": "Task 3", "branch": "feature/task-3"}
    ],
    "execution_mode": "dagger",
    "max_concurrent": 4
  }'
```

## Architecture

### Pipeline Mode (Isolated)

```
┌─────────────────────────────────────────────────────────────────┐
│  Your Mac (local repo UNCHANGED)                                │
│                                                                 │
│  ~/.claude-container/.credentials.json                          │
│        │                                                        │
│  ┌─────│────────────────────────────────────────────────────┐   │
│  │  Docker / Dagger                                         │   │
│  │     │                                                    │   │
│  │  ┌──▼───────────────────────────────────────────────┐   │   │
│  │  │ Container                                         │   │   │
│  │  │  • Clone from GitHub (fresh, isolated)           │   │   │
│  │  │  • Run Claude Code                               │   │   │
│  │  │  • Commit changes                                │   │   │
│  │  │  • Push to GitHub ─────────────────────────────────────► │
│  │  │  • Container discarded                           │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  [Agent 2]  [Agent 3]  [Agent 4]  ... (parallel)        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ✅ Local repo unchanged                                        │
│  ✅ Multiple branches in parallel                               │
│  ✅ No merge conflicts                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Testing Mode (Synced)

```
┌─────────────────────────────────────────────────────────────────┐
│  Your Mac                                                       │
│                                                                 │
│  Local Repo ◄─────────────────┐                                │
│       │                        │ sync back                      │
│       │ mount                  │                                │
│  ┌────▼────────────────────────│───────────────────────────┐   │
│  │  Container                  │                            │   │
│  │  • Mounted local repo       │                            │   │
│  │  • Run Claude Code          │                            │   │
│  │  • Changes synced back ─────┘                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ⚠️  Only one agent at a time (git conflicts)                  │
│  ✅ Fast iteration for testing                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Mode Comparison

| Feature | local | dagger (pipeline) | dagger (testing) |
|---------|-------|-------------------|------------------|
| Cost | FREE | **FREE** | **FREE** |
| Parallel | ❌ | **✅** | ❌ |
| Isolation | ❌ | **✅** | ❌ |
| Speed | Fast | **Fast (~8s)** | Fast |
| Offline | ✅ | ✅ | ✅ |
| Auth | Keychain | OAuth | OAuth |
| Local Changes | ✅ | **❌** | ✅ |

**Pipeline mode is best for**: Autonomous execution, parallel agents, CI/CD
**Testing mode is best for**: Development iteration, quick experiments

## Implementation Details

### Container Setup
- Base image: `node:20-slim`
- Non-root user: `agent` (Claude Code requires non-root for `--dangerously-skip-permissions`)
- Git configured with `agent@commandcenter.ai`
- OAuth credentials injected via Dagger secrets (not env vars or mounts)

### Security
- GitHub token passed via Dagger secrets (never logged)
- URLs sanitized in logs (tokens hidden)
- Credentials read from `~/.claude-container/` (not `~/.claude/` which macOS Claude deletes)

### Error Handling
- Container sync refused if >20 deletions detected (corruption protection)
- Failed agents don't sync back (prevents corrupted state)
- Push failures logged but don't crash the session

## Troubleshooting

### "Docker not running"
```bash
open -a Docker  # Start Docker Desktop
```

### "Dagger SDK not found"
```bash
pip install dagger-io
```

### "No credentials found"
```bash
# First, authenticate locally
claude
# Complete OAuth login

# Then export credentials
./scripts/export-claude-credentials.sh
```

### "Authentication failed" in container
Credentials may have expired. Re-run:
```bash
./scripts/export-claude-credentials.sh
```

### Push failed from container
Check GitHub token is available:
```bash
gh auth status  # Should show logged in
gh auth token   # Should output a token
```

### Local repo modified unexpectedly
You may have used testing mode (no branch). For pipeline isolation, always specify a branch.

## Pre-flight Check

```bash
# 1. Credentials exist
test -f ~/.claude-container/.credentials.json && echo "✅ Credentials" || echo "❌ Run export script"

# 2. Docker running
docker info > /dev/null 2>&1 && echo "✅ Docker" || echo "❌ Start Docker"

# 3. GitHub auth
gh auth status > /dev/null 2>&1 && echo "✅ GitHub" || echo "❌ Run: gh auth login"

# 4. Dagger SDK
python -c "import dagger" 2>/dev/null && echo "✅ Dagger SDK" || echo "❌ Run: pip install dagger-io"
```

## Related

- `backend/app/services/agent_service.py` - Implementation (`_execute_dagger` method)
- `scripts/export-claude-credentials.sh` - Credential export script
- `docs/plans/cc3-full-mvp-01-10.md` - MVP execution plan
