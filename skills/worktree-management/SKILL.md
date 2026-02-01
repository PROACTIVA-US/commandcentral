---
status: active
name: worktree-management
description: Manage git worktrees for parallel pipeline execution. Check before pipeline
  runs, after failures, or when startup is slow.
priority: P0
updated: 2026-01-15 17:35
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
# Worktree Management

**This skill ensures worktrees are properly configured for the autonomous pipeline.**

## Essence (50 words)

Worktrees at `CC4-worktrees/` (gitignored, inside project). ALWAYS push main to origin BEFORE pipeline. Worktrees reset to origin/main between tasks. Cleanup: `git fetch && git reset --hard origin/main && git clean -fdx`. Pool reuses existing worktrees for fast startup (~200ms vs 8+ minutes).

---

## Quick Commands

### Check Worktree Status
```bash
cd /Users/danielconnolly/Projects/CC4
git worktree list
```

### Force Clean All Worktrees
```bash
for wt in wt-1 wt-2 wt-3; do
  cd /Users/danielconnolly/Projects/CC4/CC4-worktrees/$wt
  git fetch origin main --quiet
  git reset --hard origin/main
  git clean -fdx
  echo "$wt cleaned: $(git log --oneline -1)"
done
```

### Verify origin/main is Current
```bash
cd /Users/danielconnolly/Projects/CC4
git fetch origin
git log --oneline main -1
git log --oneline origin/main -1
# If different: git push origin main
```

---

## Critical Rules

### 1. ALWAYS Push Before Pipeline
```bash
# Before ANY pipeline run:
git push origin main

# Verify:
git log --oneline origin/main -1  # Should match local main
```

**Why:** Worktrees reset to `origin/main`. If local is ahead, worktrees get stale code.

### 2. Worktrees Are Gitignored
Location: `/Users/danielconnolly/Projects/CC4/CC4-worktrees/`

Already in `.gitignore`:
```
CC4-worktrees/
```

### 3. Pool Reuses Existing Worktrees
On startup, the pool checks if worktrees exist and reuses them:
- **Fast startup:** ~200ms (reuse existing)
- **Slow startup:** 8+ minutes (create new)

If startup is slow, worktrees may have been deleted. Let them recreate once.

### 4. Cleanup Between Tasks
Each task should start with clean worktree. Cleanup script:
```bash
git fetch origin main --quiet
git rebase --abort 2>/dev/null || true
git merge --abort 2>/dev/null || true
git checkout -f worktree-wt-N
git reset --hard origin/main
git clean -fdx
```

---

## Troubleshooting

### Worktree Has Leftover Files
```bash
cd CC4-worktrees/wt-1
git status  # Check what's dirty
git reset --hard origin/main
git clean -fdx
```

### Worktrees on Wrong Commit
```bash
# Check current commit
git log --oneline -1

# Should match origin/main
git log --oneline origin/main -1

# If not, force reset:
git fetch origin main
git reset --hard origin/main
```

### "database is locked" Errors
1. Check for stale Python processes:
   ```bash
   lsof backend/data/cc4.db
   ```
2. Kill stale processes:
   ```bash
   kill -9 <PID>
   ```
3. Remove stale journal:
   ```bash
   rm -f backend/data/cc4.db-journal
   ```

### Slow Startup (8+ minutes)
Worktrees are being recreated. Check:
```bash
ls -la CC4-worktrees/
```

If empty, let pool recreate once. Future startups will be fast.

---

## Architecture

### Pool Configuration
- **Location:** `../CC4-worktrees` (relative to backend/)
- **Pool size:** 3 worktrees (wt-1, wt-2, wt-3)
- **Branches:** `worktree-wt-1`, `worktree-wt-2`, `worktree-wt-3`

### Files
- `backend/app/services/worktree_pool.py` - Pool management
- `backend/app/services/parallel_execution_runner.py` - Worker management
- `backend/app/startup.py` - Pool initialization

### Lifecycle
1. **Startup:** Pool initializes, reuses or creates worktrees
2. **Acquire:** Worker gets free worktree, marks BUSY
3. **Execute:** Task runs in worktree isolation
4. **Release:** Worktree cleaned, marked FREE
5. **Shutdown:** Pool cleans worktrees (preserves for reuse)

---

## Pre-Pipeline Checklist

Before running autonomous pipeline:

- [ ] `git push origin main` - Push latest changes
- [ ] `git log origin/main -1` - Verify origin is current
- [ ] `git worktree list` - Check worktrees exist
- [ ] No stale Python processes on database
- [ ] Backend running WITHOUT `--reload`

---

*Worktrees enable parallel execution. Keep them clean, keep origin current.*
