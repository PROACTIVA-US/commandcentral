---
name: long-running-agents
description: Execute complex tasks across multiple agent sessions with PR review workflow
spec_source: docs/specs/commandcenter3.md
spec_section: "4.7 Long-Running Agent Orchestrator"
related_documents:
  - docs/guides/aef-execution-guide.md
  - docs/plans/document-to-done-pipeline.md
implementation:
  - backend/app/services/long_running_orchestrator.py
  - backend/app/services/progress_protocol.py
  - backend/app/routers/agents.py
---

# Long-Running Agents

Run autonomous tasks that exceed a single context window by orchestrating multiple fresh sessions with state handoff and code review.

## The Problem

Single-session agents fail on complex tasks because:
- Context window fills up (~200k tokens)
- Auto-compact loses important details
- Agent declares "done" before actually completing
- No code review catches bugs early

## The Solution

**Multi-session architecture with PR review workflow:**

```
┌─────────────────────────────────────────────────────────────────┐
│  INITIALIZER (Session 1 - on main)                              │
│  - Creates AGENT_PROGRESS.md with goal & criteria               │
│  - Breaks task into incremental steps                           │
│  - Commits scaffolding to main                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CODER #1 (on branch: agent/step-1-xxx)                         │
│  - Reads AGENT_PROGRESS.md                                      │
│  - Picks ONE task from "Next Steps"                             │
│  - Completes it, updates progress file, commits                 │
│  - Branch pushed, PR created                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  REVIEWER (fresh context)                                       │
│  - Reviews the PR diff                                          │
│  - Runs tests                                                   │
│  - Approves or requests changes with specific feedback          │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
        [Issues Found]                  [Approved]
              │                               │
              ▼                               ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│  FIXER (same branch)    │    │  MERGE PR               │
│  - Addresses feedback   │    │  - Squash merge to main │
│  - Commits fixes        │    │  - Delete branch        │
│  - Back to REVIEWER     │    │  - Pull latest main     │
└─────────────────────────┘    └─────────────────────────┘
                                             │
                                             ▼
                                      CODER #2 ...
```

## API Usage

### Start a Long-Running Task (with PR workflow)

```bash
curl -X POST http://localhost:8001/api/v1/agents/run-long \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Implement user authentication with OAuth",
    "success_criteria": [
      "Users can sign up with email/password",
      "Users can log in and receive JWT token",
      "Protected routes require valid token",
      "All tests pass"
    ],
    "max_sessions": 15,
    "model": "sonnet",
    "execution_mode": "dagger",
    "use_pr_workflow": true,
    "max_review_rounds": 3
  }'
```

Response:
```json
{
  "task_id": "abc123",
  "status": "running",
  "use_pr_workflow": true,
  "message": "Long-running task started with up to 15 sessions (PR + review workflow enabled)"
}
```

### Simple Mode (no PRs, direct commits)

```bash
curl -X POST http://localhost:8001/api/v1/agents/run-long \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Quick prototype task",
    "success_criteria": ["Feature works"],
    "use_pr_workflow": false
  }'
```

### Check Status

```bash
curl http://localhost:8001/api/v1/agents/long-tasks/{task_id}
```

Response (completed):
```json
{
  "task_id": "abc123",
  "status": "completed",
  "total_sessions": 12,
  "total_duration_seconds": 2847.5,
  "pr_cycles": [
    {"branch": "agent/step-1-1704650000", "pr_url": "https://github.com/.../pull/42", "merged": true, "review_rounds": 2},
    {"branch": "agent/step-2-1704650500", "pr_url": "https://github.com/.../pull/43", "merged": true, "review_rounds": 1}
  ],
  "criteria_met": {
    "Users can sign up with email/password": true,
    "Users can log in and receive JWT token": true,
    "Protected routes require valid token": true,
    "All tests pass": true
  }
}
```

### Stop a Task

```bash
curl -X POST http://localhost:8001/api/v1/agents/long-tasks/{task_id}/stop
```

## The PR Cycle

Each coding cycle follows this flow:

```
1. Create branch from main
   └── git checkout -b agent/step-N-timestamp

2. Coder agent works
   └── Makes changes, updates AGENT_PROGRESS.md, commits

3. Push and create PR
   └── git push, gh pr create

4. Review loop (up to max_review_rounds)
   ├── Reviewer checks diff, runs tests
   ├── If issues: Fixer addresses feedback
   └── Repeat until approved or max rounds

5. Merge
   └── Squash merge, delete branch, pull main

6. Next cycle starts from updated main
```

## The Progress File (AGENT_PROGRESS.md)

```markdown
# AGENT_PROGRESS.md

## Project Goal
Implement user authentication with OAuth

## Success Criteria
- [x] Users can sign up with email/password
- [x] Users can log in and receive JWT token
- [ ] Protected routes require valid token
- [ ] All tests pass

## Current Status
Phase: 3 of 5
Last Agent: session-abc123
Last Action: Implemented JWT token generation

## Completed Work
1. [2026-01-07 14:30] Set up project structure - session-init
2. [2026-01-07 14:45] Added User model and signup endpoint - session-abc (PR #42)
3. [2026-01-07 15:02] Implemented JWT token generation - session-def (PR #43)

## Next Steps (for next agent)
1. Add authentication middleware for protected routes
2. Write integration tests for auth flow
3. Add password reset email flow

## Blockers / Notes
- Using bcrypt for password hashing
- JWT secret stored in environment variable
```

## Key Principles

### 1. Incremental Progress
Each session does ONE thing well, not many things partially.

### 2. Code Review
Every change goes through review. Reviewer catches bugs, suggests improvements.

### 3. Fix Loop
If reviewer finds issues, fixer addresses them before merge. Up to N rounds.

### 4. State in Git
- `AGENT_PROGRESS.md` tracks logical state
- Git history + PRs track actual code changes
- Fresh sessions reconstruct context from these artifacts

### 5. Fresh Context Every Session
No context exhaustion. Each session (coder, reviewer, fixer) gets full 200k tokens.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `goal` | required | What to accomplish |
| `success_criteria` | required | Verifiable completion criteria |
| `max_sessions` | 20 | Max total sessions |
| `model` | sonnet | Model for coding/review |
| `execution_mode` | dagger | dagger (isolated) or local |
| `use_pr_workflow` | true | Enable PR + review cycle |
| `max_review_rounds` | 3 | Max review/fix cycles per PR |
| `session_timeout` | 600 | Seconds per session |

## When to Use PR Workflow

**Use PR workflow (`use_pr_workflow: true`) for:**
- Production code
- Complex features
- Team projects
- Quality-critical work

**Use simple mode (`use_pr_workflow: false`) for:**
- Quick prototypes
- Personal experiments
- Simple tasks
- Speed over quality

## Writing Good Success Criteria

**Good criteria are:**
- Verifiable by running code/tests
- Binary (met or not met)
- Independent where possible

**Examples:**

✅ Good:
- "Users can POST to /api/signup and receive 201 response"
- "Running `pytest tests/auth/` passes all tests"
- "Database has users table with email, password_hash columns"

❌ Bad:
- "Authentication is well-implemented"
- "Code is clean and maintainable"
- "User experience is good"

## Troubleshooting

### PR creation fails
- Ensure `gh` CLI is installed and authenticated
- Check GitHub token has repo permissions

### Review always requests changes
- Make success criteria more specific
- Reviewer may be too strict - check the feedback

### Merge conflicts
- Task may have drifted from main
- Consider smaller incremental steps

### Sessions timing out
- Increase `session_timeout`
- Break task into smaller steps

## Comparison

| Aspect | Simple Mode | PR Workflow |
|--------|-------------|-------------|
| Speed | Faster | Slower |
| Quality | Lower | Higher |
| Review | None | Every change |
| Recovery | Harder | Easier (branches) |
| Audit trail | Commits only | PRs + reviews |

## Related

- `skills/dagger-execution/SKILL.md` - Container execution
- `docs/decisions/dagger-library-mode-2026-01-07.md` - Why library mode
- Anthropic: "Effective harnesses for long-running agents"
