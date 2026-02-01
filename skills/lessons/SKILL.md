---
status: active
name: lessons
description: Hard-won lessons and anti-patterns - mistakes that wasted hours. Check
  before debugging pipeline issues.
priority: P0
updated: 2026-01-18 12:02
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
# Lessons Learned

**This skill captures hours of wasted debugging.** Read before making similar mistakes.

## Essence (50 words)

NEVER --reload for autonomous. Local mode = sequential (git race). PATH needs /opt/homebrew/bin. Sync DB for background tasks. Verify problems before fixing. Check skills before work. Don't intervene during execution. **ALWAYS push main to origin before running pipeline.** Pipeline works - trust it. **SKILLS NOW ENFORCED VIA HOOKS (2026-01-12).** **CHECK SPEC-IMPLEMENTATION ALIGNMENT PERIODICALLY** - specs drift. **CAPTURE KNOWLEDGE ACTIVELY** - don't wait to be reminded. **TASK COMPLETION DETECTION REQUIRES TWO SIGNALS** - single pattern match causes false positives. **FRONTEND PORT IS 3002** - configured in vite.config.ts, NOT default 5173.

---

## Incident: Frontend Port Assumption (2026-01-18) [LESSON]

### What Happened
When testing optimizations, attempted to navigate to http://localhost:5173 (Vite default port) instead of the actual frontend port 3002.

### Root Cause
Assumed Vite default port without checking project configuration.

### The Fix
**ALWAYS check vite.config.ts for actual port configuration.** CC4 frontend is configured to run on port 3002, not the Vite default of 5173.

**Configuration:**
```typescript
// frontend/vite.config.ts
export default defineConfig({
  server: {
    port: 3002,  // ← Not 5173!
    proxy: {
      '/api': { target: 'http://localhost:8001' },
      '/ws': { target: 'ws://localhost:8001', ws: true }
    }
  }
})
```

### Detection
1. Check if frontend is running: `lsof -i :3002 | grep LISTEN`
2. Verify port in vite.config.ts:7
3. Backend API is at localhost:8001
4. Frontend UI is at localhost:3002

### Lesson
> **Check vite.config.ts for actual port, don't assume Vite defaults.** CC4 uses port 3002 for frontend.

---

## Incident: Task Completion Detection False Positives (2026-01-15) [FIXED]

### What Happened
Pipeline marked 44 tasks as "already completed" when they weren't. Tasks showed "✅" in title but had no actual work done. Two separate executions ran the same plan, with many tasks falsely skipped.

### Root Cause
The `_check_task_completion` method in `batch_orchestrator.py` was too loose:
1. **Pattern "1.1" matched "Batch 1.1"** from a completely different old plan
2. **Just 2 title words matching** was enough to mark complete
3. **Single signal = complete** - no secondary confirmation required

### The Fix
Changed detection to require **TWO OR MORE signals**:
```python
# Now requires multiple confirmations:
if task_number_matched AND title_matched: return True
if task_number_matched AND files_exist: return True
if title_matched AND files_exist: return True
# Single signal = NOT complete (prevents false positives)
```

Also:
- Stricter task number patterns: "Task 1.1:" not just "1.1"
- Expanded common words filter: excludes "create", "model", "service", etc.
- Require 3+ significant title words to match

### Detection
Found 44 tasks marked "merged" with no PR URLs - all had `skipped_reason: "Already completed in git history"` but git log showed no matching commits for actual work.

### Lesson
> **Pattern matching across git history is dangerous.** Task numbers from old plans collide with new plans. Always require multiple signals to confirm completion.

### Prevention
- Task completion requires 2+ signals (number+title, number+files, or title+files)
- Common words filtered from title matching
- Single pattern match logs warning but doesn't skip task

---

## Incident: Spec-Implementation Fundamental Misalignment (2026-01-15) [CRITICAL]

### What Happened
CC4 spec v2.2 described a "belief validation engine" (Goals, Hypotheses, Evidence, Confidence). The actual implementation was an "autonomous execution platform" (Projects, Tasks, Pipeline). **25% alignment** - essentially two different systems.

External reviews (Grok, OpenAI) independently identified:
- Missing core entities (Goals, Assessments, Confidence Engine)
- Phase estimates 2-3x too optimistic
- Undefined contracts (assessment aggregation, event sourcing)

### Root Cause
1. **Spec written aspirationally** - described the vision, not what was being built
2. **No periodic alignment checks** - spec and implementation drifted apart
3. **Wrong evidence model** - Evidence table was FedRAMP compliance, not strategic intelligence

### The Fix
1. **Added two-layer architecture** (Section 2) - Layer 1 (Execution, 95% built), Layer 2 (Intelligence, 5% built)
2. **Honest implementation status** - component-by-component breakdown
3. **MVP scope defined** - 150 hours for core loop before automation
4. **External review integration** - addressed all BLOCKER issues
5. **3x estimate adjustment** - 242 → 726 hours total

### Detection
Multiple external reviewers converging on same issues is a strong signal. When Grok AND OpenAI both say "2-3x longer" - believe them.

### Lesson
> **Specs must describe what IS, not just what SHOULD BE.** Add implementation status section. Run external reviews. Check alignment periodically. Don't let specs become fiction.

### Prevention
- Add "Implementation Status" section to all specs
- Run external reviews before major work phases
- Quarterly spec-implementation alignment checks
- When estimates seem optimistic, triple them

---

## Incident: Knowledge Capture Neglected (2026-01-15) [MEDIUM]

### What Happened
During spec revision work, skills/lessons were not being updated. User had to explicitly ask "are we capturing knowledge?" before it happened.

### Root Cause
1. **Task focus over meta-work** - focused on spec edits, not knowledge capture
2. **No automatic trigger** - nothing reminded to update lessons after significant work
3. **Timestamps fabricated** - made up "14:00" instead of checking actual time (13:12)

### The Fix
1. **Update lessons immediately** after significant debugging or discovery
2. **Always check actual time** - `date "+%Y-%m-%d %H:%M"` before writing timestamps
3. **Review skills governance** - check if current work should update existing skills

### Lesson
> **Knowledge capture is part of the work, not an afterthought.** Update lessons in real-time. Check actual timestamps. Skills that don't evolve become stale.

---

## Incident: Feature Branches Created from Stale origin/main (2026-01-14) [CRITICAL]

### What Happened
Pipeline created 3 PRs (Batch 1 tasks) that attempted to **delete the entire CC4 codebase**. Each PR showed ~200 deletions including all frontend, backend, docs, and skills.

### Root Cause
**Local main was 19 commits ahead of origin/main.** Sequence:
1. Phase 1 & 2 work committed locally to main (19 commits)
2. Local main **never pushed to origin**
3. origin/main stuck at initial commit (01e5c9b)
4. Pipeline ran and executed: `git fetch origin main` + `git reset --hard origin/main`
5. Feature branches created from origin/main = 01e5c9b (first commit)
6. When merged, these branches would delete everything added after 01e5c9b

**The pipeline code was correct** - it fetched and reset to origin/main as designed. The bug was **operator error**: forgetting to push local work to origin.

### The Fix
1. Closed all 3 broken PRs with explanation
2. Deleted broken feature branches from origin
3. **Pushed local main to origin** (`git push origin main`)
4. Cleaned up worktrees (wt-1, wt-2, wt-3)
5. Verified origin/main now matches local main

### Detection
Feature branches based on commit 01e5c9b while main was at de8c9c3. Git diff showed branches **deleting** all project files instead of adding new ones.

### Lesson
> **ALWAYS verify origin/main is up-to-date before running pipeline.** Check `git status` shows "up to date with origin/main" not "ahead by N commits". Pipeline assumes origin/main is the source of truth.

### Prevention
Add pre-pipeline check:
```bash
# Before running pipeline
git fetch origin
BEHIND=$(git rev-list HEAD..origin/main --count)
AHEAD=$(git rev-list origin/main..HEAD --count)

if [ "$AHEAD" -gt 0 ]; then
    echo "ERROR: Local main is $AHEAD commits ahead of origin/main"
    echo "Run: git push origin main"
    exit 1
fi
```

---

## Incident: Skills Being Ignored (2026-01-12) [RESOLVED]

### What Happened
Despite having 9 active skills with clear governance, agents repeatedly:
1. Create redundant docs instead of updating existing
2. Place files in wrong locations
3. Ignore documentation-protocol naming conventions
4. Create new plans instead of updating MASTER_PLAN
5. Ignore timestamp format requirements

### Root Cause
Skills are referenced but not enforced. The system relies on agents voluntarily reading skills, but:
- Context pressure makes agents skip "optional" reads
- No hard enforcement via hooks or validation
- CLAUDE.md says "read skills" but nothing verifies compliance

### The Fix (IMPLEMENTED 2026-01-12 16:50)

**1. Git Pre-commit Hook** (`.git/hooks/pre-commit`):
   - Blocks unauthorized `.md` files in root
   - Validates frontmatter in all `docs/` files
   - Enforces timestamp format (YYYY-MM-DD HH:MM)
   - Prevents new plan files (only MASTER_PLAN.md allowed)
   - Blocks test scripts and utility scripts in root

**2. Claude Code PreToolUse Hook** (`.claude/hooks/PreToolUse/skill_check.sh`):
   - Blocks file creation violations in real-time
   - Validates frontmatter on Write operations
   - Enforces repository-hygiene patterns
   - Provides immediate feedback before commit

**3. Prompt Injection** (CLAUDE.md):
   - Critical skill content injected directly into CLAUDE.md
   - No longer relies on agents reading separate skill files
   - Rules are visible in every session automatically

**Testing Results:**
- ✅ Blocked unauthorized .md file in root
- ✅ Blocked test script in root
- ✅ Blocked invalid timestamp format
- ✅ Allowed valid commits to proceed

### Lesson
> Skills without enforcement are suggestions. Make compliance mandatory via hooks.
> **UPDATE:** Enforcement now active. Violations are impossible, not optional.

---

## Incident: --reload Kills Background Tasks (2026-01-12) [CRITICAL]

### What Happened
Autonomous pipeline tasks would create files but never commit. Tasks stuck in "executing" state.

### Root Cause
`uvicorn --reload` detects file changes and restarts the server. When an agent creates files, the server restarts, killing the background task mid-execution.

### The Fix
**NEVER use --reload for autonomous execution:**
```bash
# WRONG - kills background tasks
uvicorn app.main:app --port 8001 --reload

# CORRECT
uvicorn app.main:app --port 8001
```

### Lesson
> --reload + background tasks = disaster. Use plain uvicorn for autonomous.

---

## Incident: Git Race Condition in Parallel Tasks (2026-01-12) [CRITICAL]

### What Happened
Only 1 of 3 tasks succeeded. Others failed with "No commits between main and branch" or branch corruption.

### Root Cause
`max_concurrent=4` allowed multiple tasks to run `git checkout` on the same repo simultaneously. Task A checks out branch-1, Task B checks out branch-2 (corrupting Task A's state), etc.

### The Fix
Force sequential execution in local mode (`task_executor.py` line 839):
```python
if execution_mode == "local":
    max_concurrent = 1  # Forced to prevent git race
```

For parallel execution, use `"execution_mode": "dagger"` where each task runs in an isolated container with its own repo clone.

### Lesson
> Parallel git operations on same repo = corruption. Sequential or isolated containers.

---

## Incident: Claude CLI Not Found (2026-01-12)

### What Happened
Agent tasks failed immediately with "Claude CLI not found" even though `claude` worked in terminal.

### Root Cause
`subprocess` doesn't inherit shell PATH expansions. `/opt/homebrew/bin` (where Claude CLI lives) wasn't in the PATH when running via subprocess.

### The Fix
Explicitly add homebrew to PATH in `agent_service.py` (lines 338-339):
```python
if "/opt/homebrew/bin" not in current_path:
    os.environ["PATH"] = f"/opt/homebrew/bin:/usr/local/bin:{current_path}"
```

### Lesson
> subprocess PATH ≠ shell PATH. Add tool directories explicitly.

---

## Incident: Manual Intervention Corrupts Pipeline (2026-01-12)

### What Happened
Manually committed agent work to main, then reverted. Subsequent pipeline runs failed with "No commits between branches."

### Root Cause
Manual intervention pollutes git state. When I committed files the agent was supposed to create, then reverted, the branch history got confused.

### The Fix
**NEVER manually intervene during autonomous execution.** Let it complete or fail, then fix.

### Lesson
> Hands off during execution. Fix AFTER completion.

---

## Incident: Pipeline Hardening (2026-01-09)

### What Happened
Hours spent creating a 300-line "pipeline hardening" plan to fix problems that:
1. Didn't exist
2. Were already solved in skills

### Root Cause
Claude Code didn't read `commandcenter-operations` or `dagger-execution` skills before starting work.

### The Fix
**ALWAYS check skills BEFORE starting any task involving:**
- Pipeline execution
- Agent service changes
- Dagger/container work
- Branch/merge operations

### Lesson
> Read skills first. They contain solved problems.

---

## Incident: venv Corruption Scare (2026-01-11)

### What Happened
Investigation into "venv corruption" that turned out to be healthy all along.

### Root Cause
Hypothesis without evidence. "Corruption" was documented as a *concern*, not actual evidence.

### The Fix
**Verify issues exist before fixing:**
```bash
python -c "import sys; print(sys.executable)"
pip list | wc -l  # Should show 100+ packages
```

### Lesson
> Diagnose before planning. Run verification commands first.

---

## Incident: Context Overload (2026-01-11)

### What Happened
Context jumping erratically (10% → 90% → 15%). Claude Code becoming slow/unresponsive.

### Root Cause
- 35+ skills auto-loading
- 8 MCP servers connecting simultaneously
- Heavy plugins (superpowers, compound-engineering)
- 55+ agents loading at startup

### The Fix
1. Consolidated 35 skills → 3
2. Disabled unused MCP servers in `~/.claude/mcp.json`
3. Removed heavy plugins

### Lesson
> Less is more. Skills should be minimal, not comprehensive manuals.

---

## Incident: Context Shows 0% (2026-01-11)

### What Happened
Claude Code context indicator stuck at 0%.

### Possible Causes
1. Debug mode settings affecting display
2. Plugin interference
3. Session corruption after `/clear`

### The Fix
Check `~/.claude/settings.json` and disable unused features.
Start fresh session if needed.

### Lesson
> When metrics seem wrong, check settings first.

---

## Anti-Patterns

### 1. Fixing Before Verifying
```
❌ "I'll write a plan to fix the corruption"
✅ "Let me first verify if corruption exists"
```

### 2. Skipping Skills
```
❌ "This is a quick fix, I don't need skills"
✅ "Let me check if this is already solved"
```

### 3. Skill Proliferation
```
❌ "I'll create a skill for each topic"
✅ "I'll add to existing skills or lessons"
```

### 4. Comprehensive Documentation in Skills
```
❌ 1000-line skill with every edge case
✅ 200-line skill with essence + key points
```

### 5. Ignoring Pre-flight Checks
```
❌ Jump straight into pipeline execution
✅ Run pre-flight: Docker? Backend? Creds?
```

---

## Incident: SQLAlchemy Async Greenlet Error (2026-01-11) [RESOLVED]

### What Happened
Autonomous pipeline blocked by SQLAlchemy async error in background tasks:
```
greenlet_spawn has not been called; can't call await_only() here
```

### Root Cause
`asyncio.create_task()` doesn't propagate greenback portal to child tasks. SQLAlchemy async requires greenlet context.

### The Fix (IMPLEMENTED)
1. Created `get_sync_db()` context manager in `database.py`
2. Rewrote `execution_runner.py` to use sync DB operations via `asyncio.to_thread()`
3. Added `execute_batch_tasks_sync()` and `SyncTaskExecutor` to `task_executor.py`
4. Fixed `commands.py` background task to use sync session

Key code:
```python
# database.py
@contextmanager
def get_sync_db() -> Generator[Session, None, None]:
    session = sync_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# In background tasks, use:
with get_sync_db() as db:
    # sync DB operations here
```

### Lesson
> Async SQLAlchemy + background tasks = greenlet hell. Use sync ops for background work.

---

## Incident: Local Mode Pipeline Failures (2026-01-12) [MEDIUM]

### What Happened
Phase 4 Batch 1 execution failed with multiple issues:
1. Task 4.1.1: "No commits between main and feature branch" (PR creation failed)
2. Task 4.1.2: Push rejected - remote branch already existed
3. Task 4.1.3: Dirty working directory prevented branch checkout
4. All tasks: "ruff check ." verification failed on pre-existing code issues

### Root Causes

**1. Agent pre-commits breaking push flow** (`_commit_and_push`):
- Agent commits changes itself during execution
- `_commit_and_push` checks for uncommitted changes, finds none, returns early
- Branch never gets pushed to remote
- **Fixed in fe3c208**

**2. Dirty working directory between tasks**:
- Task leaves uncommitted changes when it fails
- Next task can't checkout its branch
- **Fixed in fe3c208** - added cleanup before branch creation

**3. Own-PR review error**:
- GitHub rejects REQUEST_CHANGES on your own PR
- Pipeline crashed instead of falling back to COMMENT
- **Fixed in fe3c208** - catches error and uses COMMENT

**4. Verification scope too broad** (STILL UNFIXED):
- `ruff check .` runs on entire codebase
- Fails on pre-existing lint issues unrelated to current task
- Should only verify changed files

**5. Already-done task handling** (STILL UNFIXED):
- When task code already exists, agent makes no changes
- PR creation fails with "no commits between branches"
- Should skip or mark task as complete

### The Fixes Applied
```python
# task_executor.py - Clean working directory before branch creation
async def _create_branch(self, branch_name: str) -> None:
    # Step 1: Clean working directory
    subprocess.run(["git", "checkout", "main"], ...)
    subprocess.run(["git", "reset", "HEAD"], ...)
    subprocess.run(["git", "checkout", "--", "."], ...)
    subprocess.run(["git", "clean", "-fd"], ...)
    # Step 2: Create branch...

# task_executor.py - Always push even if no new commits
async def _commit_and_push(...):
    if files_changed:
        # commit...
    else:
        logger.info("No uncommitted changes - agent may have already committed")
    # ALWAYS push (moved outside the if block)
    subprocess.run(["git", "push", "-u", "origin", branch_name], ...)

# pr_reviewer.py - Handle own-PR review limitation
except GithubException as create_error:
    if "request changes on your own" in str(create_error).lower():
        # Fall back to COMMENT event
        review = pr.create_review(body=body, event="COMMENT", ...)
```

### All Issues Fixed (2026-01-12)
1. ✅ Verification now only checks modified files (`git diff --name-only origin/main`)
2. ✅ Skip PR creation when no commits on branch (task already complete)
3. ✅ Delete remote/local branches before creating fresh branch
4. ✅ Task status now updates in DB even on batch-level exceptions

### Lesson
> Local mode has many edge cases. Trust Dagger mode for production - it's isolated and parallel.

---

## Incident: Background Tasks Never Execute (2026-01-12) [CRITICAL - FIXED]

### What Happened
E2E test revealed that autonomous execution API would accept requests and create database records, but background tasks never actually executed. The ExecutionRunner.run() method was never called despite asyncio.create_task() being invoked.

**Symptoms:**
- API returns 200 OK with execution ID
- Database shows session and tasks created
- Tasks remain in "pending" or "in_progress" forever
- No execution logs appear
- No Dagger containers created

### Root Cause
**asyncio.create_task() doesn't immediately schedule tasks.** When you create a task with `asyncio.create_task()`, it registers the task with the event loop but doesn't run it immediately. The task only gets scheduled when the event loop gets control back.

In our API endpoint flow:
1. API handler calls `start_background_execution()`
2. `asyncio.create_task(runner.run())` is called
3. API handler returns immediately
4. Event loop never yields, so task never runs

This is a subtle asyncio behavior - the task is created but sits in the event loop's queue, waiting for the current coroutine to yield control.

### The Fix (IMPLEMENTED)

**Add `await asyncio.sleep(0)` after creating the task:**

```python
# execution_runner.py - start_background_execution()

# Create task and store reference to prevent GC
task = asyncio.create_task(runner.run())
_background_tasks.add(task)

# CRITICAL: Yield to event loop to allow task scheduling
# Without this, asyncio.create_task() creates the task but it never runs
# because the event loop doesn't get a chance to schedule it.
await asyncio.sleep(0)
```

**Why this works:**
- `await asyncio.sleep(0)` yields control to the event loop
- Event loop can now schedule and start the background task
- Task begins executing while the API response is being sent

### Testing Results
**Before fix:**
- ❌ ExecutionRunner.run() never called
- ❌ No log output from background execution
- ❌ Tasks stuck in "pending" forever

**After fix:**
- ✅ ExecutionRunner.run() is called immediately
- ✅ Execution logs appear
- ✅ Session progresses through states
- ✅ Background execution starts correctly

### Lesson
> `asyncio.create_task()` requires yielding to the event loop. Always add `await asyncio.sleep(0)` after creating background tasks to ensure they actually run.

**Anti-pattern:**
```python
# DON'T DO THIS - task never runs
task = asyncio.create_task(long_running_task())
return {"status": "started"}
```

**Correct pattern:**
```python
# DO THIS - task runs in background
task = asyncio.create_task(long_running_task())
await asyncio.sleep(0)  # Yield to event loop
return {"status": "started"}
```

---

## Incident: E2E Pipeline Test Failures (2026-01-12) [OPEN - BLOCKING]

### What Happened
Attempted to run E2E pipeline test to validate the full PR workflow (create → review → fix → merge). Multiple issues discovered:

**Issue 1: Dagger Mode Completes Instantly (~7 seconds)**
- Autonomous pipeline with `execution_mode: "dagger"` returns "complete" in 7 seconds
- Tasks marked as "in_progress" with no PRs, no commits, no actual work done
- Direct dagger agent execution works fine (~30 seconds for same task)
- The pipeline is not waiting for the dagger container to complete

**Issue 2: Local Mode Works But No PRs Created**
- Autonomous pipeline with `execution_mode: "local"` takes proper time (~2 minutes)
- Tasks complete but no PRs are created (pr_number: null)
- Files may or may not be created on the branch

**Issue 3: Direct Agent vs Pipeline Discrepancy**
```bash
# This works (30 seconds, creates files):
curl -X POST localhost:8001/api/v1/agents/run \
  -d '{"task": "Create formatting.py", "execution_mode": "dagger"}'

# This doesn't work (7 seconds, no changes):
curl -X POST localhost:8001/api/v1/autonomous/start \
  -d '{"plan_path": "...", "execution_mode": "dagger"}'
```

### Root Cause Analysis

**Suspected: Session Object Reference Issue**

In `task_executor.py` `_execute_with_agent()`:
```python
session = await self.agent_service.run(...)  # Returns immediately with status="pending"

while session.status in ("pending", "running"):
    await asyncio.sleep(2)  # Should yield to event loop
```

The `agent_service.run()` creates an `asyncio.create_task()` for `_execute_dagger()` and returns the session object immediately. The waiting loop should work, but:

1. The session object might not be the same reference being updated
2. The asyncio task might be failing silently before updating status
3. Something in the pipeline context prevents proper async scheduling

**Evidence:**
- Direct agent call: Session transitions pending → running → completed (30s)
- Pipeline call: Session seems to skip or immediately complete (7s)

### Workaround
Use local mode for now: `execution_mode: "local"`
- Works but is sequential (no parallel task execution)
- No git race conditions in single-task batches

### Required Fix
Debug why autonomous pipeline's dagger mode doesn't wait for task completion:
1. Add logging to `_execute_with_agent()` to trace session status changes
2. Check if the session object reference is being properly shared
3. Verify asyncio.create_task() actually runs in pipeline context
4. Consider using asyncio.wait_for() instead of polling loop

### Test Plan for Fix
```bash
# 1. Clean up
rm -f backend/app/utils/formatting.py
rm -f backend/app/tests/test_utils/test_formatting.py

# 2. Run pipeline with dagger mode
curl -X POST localhost:8001/api/v1/autonomous/start \
  -d '{"plan_path": "docs/specs/e2e-test.md", "execution_mode": "dagger"}'

# 3. Verify (should take 2+ minutes, create PRs)
curl localhost:8001/api/v1/autonomous/{exec_id}/batches
```

### Impact
- **Dagger mode (parallel execution):** BROKEN for autonomous pipeline
- **Local mode (sequential):** Works but slower
- **E2E test validation:** BLOCKED until fixed

### Lesson
> Direct API calls and pipeline calls may behave differently due to async context. Test both paths.

---

## How to Add Lessons

When you waste significant time on something:

1. **Document the incident** (what happened)
2. **Identify root cause** (why it happened)
3. **Document the fix** (how to prevent)
4. **Add to this file** with date

Format:
```markdown
## Incident: [Name] (YYYY-MM-DD)

### What Happened
[Brief description]

### Root Cause
[Why this occurred]

### The Fix
[How to prevent/solve]

### Lesson
> [One-sentence takeaway]
```

---

*Every hour wasted is a lesson earned. Document it.*
