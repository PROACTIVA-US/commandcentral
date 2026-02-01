---
status: active
name: autonomy
description: Patterns for long-running autonomous agent workflows using Ralph loop,
  stop hooks, and safety parameters. Use when tasks require persistence beyond a single
  response cycle, such as TDD loops, complex refactoring, or multi-step implementations.
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
# Autonomous Agentic Workflows

Run long-duration tasks that persist until completion using deterministic control loops.

## Core Concept

LLMs are non-deterministic. Autonomous loops use **deterministic controls** (stop hooks) to steer them toward completion. The stop hook intercepts exit attempts and re-injects the task until success criteria are met.

## When to Use

✅ **Good for:**
- Test-driven development (code → test → fix loop)
- Multi-step task lists (work through todo.md)
- Large refactoring (iterate until tests pass)
- Complex implementations (persist until done)

❌ **Not for:**
- Simple single-response tasks
- Exploratory conversations
- Tasks without clear completion criteria

### Ralph vs Manual Autonomy Decision Tree

```
Task has automated verification (tests, linters, type checkers)?
├── YES → Use Ralph Loop (automated verification is key strength)
│         └── Expected iterations > 10?
│             ├── YES → Use Ralph Loop
│             └── NO → Consider Manual Autonomy (simpler setup)
└── NO → Use Manual Autonomy (subjective work requires human judgment)

Working in standard Claude Code environment?
├── YES → Ralph Loop available
└── NO (sandbox agent, CI/CD) → Use Manual Autonomy

Task scope:
├── Single file, <10 steps → Manual Autonomy
├── Multiple files, 10+ iterations → Ralph Loop
└── Complex multi-phase → Ralph Loop with checkpoints
```

## Ralph Wiggum Loop

Ralph is the official Anthropic plugin for persistent loops.

### Basic Usage

```bash
cd ~/Projects/YourProject
claude --dangerously-skip-permissions

# Then in Claude Code:
/ralph loop "Your task description" --max-iterations 20 --completion-promise "All tests pass"
```

### Required Parameters (NON-NEGOTIABLE)

| Parameter | Purpose | Example |
|-----------|---------|---------|
| \`--max-iterations\` | Circuit breaker - prevents infinite loops | \`20\` |
| \`--completion-promise\` | Success criteria - when to stop | \`"All tests pass"\` |

**Never run Ralph without both parameters.** This prevents runaway execution.

### How It Works

1. You start \`/ralph loop "task" --max-iterations 20 --completion-promise "done"\`
2. Claude works on the task
3. When Claude tries to exit, stop hook intercepts
4. Hook checks: Is \`<promise>done</promise>\` in output AND true?
5. If no → Re-inject task, increment iteration, continue
6. If yes → Loop ends, task complete
7. If iterations >= max → Loop ends (safety stop)

### Completion Promise Rules

The promise must be:
- **Verifiable** - Can be checked programmatically or obviously
- **Specific** - Not vague ("done" vs "all 47 tests pass")
- **Honest** - Claude must NOT output false promises to escape

\`\`\`markdown
# Good promises
--completion-promise "All pytest tests pass"
--completion-promise "File docs/AUDIT.md exists with all sections complete"
--completion-promise "Zero TypeScript errors in src/"

# Bad promises
--completion-promise "Task is done"  # Too vague
--completion-promise "I tried my best"  # Not verifiable
\`\`\`

## Use Case Patterns

### Pattern 1: Test-Driven Development

\`\`\`bash
/ralph loop "Implement the UserService class. Run pytest after each change. Fix any failures." \\
  --max-iterations 30 \\
  --completion-promise "All pytest tests pass with 0 failures"
\`\`\`

Loop: Code → Test → See failures → Fix → Test → Repeat until green.

### Pattern 2: Task List Execution

Create \`todo.md\`:
\`\`\`markdown
- [ ] Add user model
- [ ] Add user router
- [ ] Add user tests
- [ ] Update API docs
\`\`\`

\`\`\`bash
/ralph loop "Work through todo.md. Mark items complete as you finish them. Commit after each item." \\
  --max-iterations 20 \\
  --completion-promise "All items in todo.md are checked"
\`\`\`

### Pattern 3: Large Refactoring

\`\`\`bash
/ralph loop "Migrate all API endpoints from v1 to v2 format. Run tests after each file." \\
  --max-iterations 50 \\
  --completion-promise "All endpoints migrated and tests pass"
\`\`\`

### Pattern 4: Documentation Generation

\`\`\`bash
/ralph loop "Generate API documentation for all routers in backend/app/routers/. Include examples." \\
  --max-iterations 15 \\
  --completion-promise "docs/API.md contains documentation for all routers"
\`\`\`

## Real-World Examples

### Example 1: TDD Loop - Authentication Feature

**Scenario:** Implementing a login endpoint with tests that initially fail.

**Command:**
\`\`\`bash
/ralph loop "Implement POST /auth/login endpoint with email/password validation. Run pytest after each change." \\
  --max-iterations 25 \\
  --completion-promise "All pytest tests in tests/test_auth.py pass"
\`\`\`

**Iteration 1 Output:**
\`\`\`bash
# Claude writes initial implementation
$ pytest tests/test_auth.py
============================= test session starts ==============================
collected 5 items

tests/test_auth.py::test_login_success FAILED                            [ 20%]
tests/test_auth.py::test_login_invalid_email FAILED                      [ 40%]
tests/test_auth.py::test_login_wrong_password FAILED                     [ 60%]
tests/test_auth.py::test_login_missing_fields FAILED                     [ 80%]
tests/test_auth.py::test_login_returns_token FAILED                      [100%]

=========================== 5 failed in 0.42s ==================================

FAILURES:
_______________________________ test_login_success _______________________________
    def test_login_success():
        response = client.post("/auth/login", json={"email": "user@example.com", "password": "pass123"})
>       assert response.status_code == 200
E       assert 404 == 200
\`\`\`

**Iteration 5 Output:**
\`\`\`bash
$ pytest tests/test_auth.py
============================= test session starts ==============================
collected 5 items

tests/test_auth.py::test_login_success PASSED                            [ 20%]
tests/test_auth.py::test_login_invalid_email FAILED                      [ 40%]
tests/test_auth.py::test_login_wrong_password PASSED                     [ 60%]
tests/test_auth.py::test_login_missing_fields PASSED                     [ 80%]
tests/test_auth.py::test_login_returns_token PASSED                      [100%]

======================== 1 failed, 4 passed in 0.38s ===========================
\`\`\`

**Iteration 7 Output (Success):**
\`\`\`bash
$ pytest tests/test_auth.py
============================= test session starts ==============================
collected 5 items

tests/test_auth.py::test_login_success PASSED                            [ 20%]
tests/test_auth.py::test_login_invalid_email PASSED                      [ 40%]
tests/test_auth.py::test_login_wrong_password PASSED                     [ 60%]
tests/test_auth.py::test_login_missing_fields PASSED                     [ 80%]
tests/test_auth.py::test_login_returns_token PASSED                      [100%]

============================== 5 passed in 0.35s ================================

<promise>All pytest tests in tests/test_auth.py pass</promise>
\`\`\`

**Result:** Loop completed in 7 iterations. All tests passing.

---

### Example 2: Task List Completion - API Endpoints

**Initial todo.md:**
\`\`\`markdown
- [ ] Add GET /users endpoint
- [ ] Add POST /users endpoint
- [ ] Add DELETE /users/:id endpoint
- [ ] Add integration tests
- [ ] Update OpenAPI schema
\`\`\`

**Command:**
\`\`\`bash
/ralph loop "Complete all tasks in todo.md. Update the file after each task. Run tests after each endpoint." \\
  --max-iterations 20 \\
  --completion-promise "All checkboxes in todo.md are marked [x]"
\`\`\`

**Iteration 3 - todo.md state:**
\`\`\`markdown
- [x] Add GET /users endpoint
- [x] Add POST /users endpoint
- [ ] Add DELETE /users/:id endpoint
- [ ] Add integration tests
- [ ] Update OpenAPI schema
\`\`\`

**Iteration 3 Output:**
\`\`\`bash
$ pytest tests/test_users.py::test_delete_user
============================= test session starts ==============================
tests/test_users.py::test_delete_user PASSED                             [100%]

============================== 1 passed in 0.18s ================================

Updated todo.md:
- [x] Add GET /users endpoint
- [x] Add POST /users endpoint
- [x] Add DELETE /users/:id endpoint
- [ ] Add integration tests
- [ ] Update OpenAPI schema
\`\`\`

**Iteration 6 - Final todo.md:**
\`\`\`markdown
- [x] Add GET /users endpoint
- [x] Add POST /users endpoint
- [x] Add DELETE /users/:id endpoint
- [x] Add integration tests
- [x] Update OpenAPI schema
\`\`\`

**Final Output:**
\`\`\`bash
$ git status
On branch feature/user-api
Changes to be committed:
  modified:   app/routers/users.py
  modified:   tests/test_users.py
  modified:   docs/openapi.yaml
  modified:   todo.md

All tasks complete!

<promise>All checkboxes in todo.md are marked [x]</promise>
\`\`\`

**Result:** Loop completed in 6 iterations. All 5 tasks finished and tested.

---

### Example 3: Refactoring Loop - Type Safety

**Command:**
\`\`\`bash
/ralph loop "Add TypeScript strict mode to src/. Fix all type errors." \\
  --max-iterations 40 \\
  --completion-promise "npm run type-check reports 0 errors"
\`\`\`

**Iteration 1 Output:**
\`\`\`bash
$ npm run type-check

> type-check
> tsc --noEmit

src/services/UserService.ts:15:23 - error TS2345: Argument of type 'string | undefined' is not assignable to parameter of type 'string'.
  Type 'undefined' is not assignable to type 'string'.

15     return this.db.find(userId);
                         ~~~~~~

src/components/Dashboard.tsx:42:18 - error TS2531: Object is possibly 'null'.

42     const name = user.profile.name;
                    ~~~~

src/utils/validation.ts:8:10 - error TS7006: Parameter 'email' implicitly has an 'any' type.

8 function validateEmail(email) {
            ~~~~~

Found 47 errors in 12 files.
\`\`\`

**Iteration 15 Output:**
\`\`\`bash
$ npm run type-check

> type-check
> tsc --noEmit

src/components/Profile.tsx:28:15 - error TS2322: Type 'number | null' is not assignable to type 'number'.
  Type 'null' is not assignable to type 'number'.

28     const age: number = user.age;
                 ~~~~~~

Found 3 errors in 2 files.
\`\`\`

**Iteration 18 Output (Success):**
\`\`\`bash
$ npm run type-check

> type-check
> tsc --noEmit

✓ No type errors found

<promise>npm run type-check reports 0 errors</promise>
\`\`\`

**Result:** Loop completed in 18 iterations. 47 type errors fixed across 12 files.

---

### Example 4: Documentation Audit

**Command:**
\`\`\`bash
/ralph loop "Audit all Python modules in src/. Ensure each has docstrings for module, classes, and public functions." \\
  --max-iterations 30 \\
  --completion-promise "pylint --disable=all --enable=missing-docstring src/ reports 0 issues"
\`\`\`

**Iteration 1 Output:**
\`\`\`bash
$ pylint --disable=all --enable=missing-docstring src/

************* Module src.services.auth
src/services/auth.py:1:0: C0114: Missing module docstring (missing-module-docstring)
src/services/auth.py:8:0: C0116: Missing function or method docstring (missing-function-docstring)
src/services/auth.py:15:4: C0116: Missing function or method docstring (missing-function-docstring)

************* Module src.models.user
src/models/user.py:1:0: C0114: Missing module docstring (missing-module-docstring)
src/models/user.py:5:0: C0115: Missing class docstring (missing-class-docstring)

------------------------------------------------------------------
Your code has been rated at 4.23/10
\`\`\`

**Iteration 12 Output (Success):**
\`\`\`bash
$ pylint --disable=all --enable=missing-docstring src/

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 6.45/10, +3.55)

<promise>pylint --disable=all --enable=missing-docstring src/ reports 0 issues</promise>
\`\`\`

**Result:** Loop completed in 12 iterations. All modules, classes, and functions documented.

---

### Example 5: Migration with Rollback Safety

**Command:**
\`\`\`bash
/ralph loop "Migrate database schema from v2 to v3. Run migration, test, rollback if issues." \\
  --max-iterations 15 \\
  --completion-promise "Migration v3 applied and all integration tests pass"
\`\`\`

**Iteration 1 Output:**
\`\`\`bash
$ npm run migrate:up

Running migration: 003_add_user_roles.sql
✓ Migration 003 applied

$ npm run test:integration

tests/integration/test_users.js
  ✓ User can be created
  ✗ User roles are assigned correctly
    Expected: ['admin', 'user']
    Received: undefined

  ✗ User permissions are checked
    TypeError: Cannot read property 'permissions' of undefined

3 tests, 1 passed, 2 failed

Detected test failures - rolling back migration...
$ npm run migrate:down
✓ Migration 003 rolled back
\`\`\`

**Iteration 4 Output (Success):**
\`\`\`bash
$ npm run migrate:up

Running migration: 003_add_user_roles.sql
✓ Migration 003 applied

$ npm run test:integration

tests/integration/test_users.js
  ✓ User can be created
  ✓ User roles are assigned correctly
  ✓ User permissions are checked

tests/integration/test_auth.js
  ✓ Authentication with roles works
  ✓ Authorization checks permissions

5 tests, 5 passed

<promise>Migration v3 applied and all integration tests pass</promise>
\`\`\`

**Result:** Loop completed in 4 iterations with automatic rollback protection.

---

## What Success Looks Like

### Successful Loop Completion

\`\`\`
🔄 Ralph Loop - Iteration 8/30
Task: Implement payment processing with Stripe integration
Promise: All payment tests pass and Stripe webhook validates

[... work performed ...]

$ pytest tests/test_payments.py -v
tests/test_payments.py::test_create_payment PASSED                       [ 14%]
tests/test_payments.py::test_capture_payment PASSED                      [ 28%]
tests/test_payments.py::test_refund_payment PASSED                       [ 42%]
tests/test_payments.py::test_webhook_signature PASSED                    [ 57%]
tests/test_payments.py::test_webhook_payment_succeeded PASSED            [ 71%]
tests/test_payments.py::test_webhook_payment_failed PASSED               [ 85%]
tests/test_payments.py::test_idempotency PASSED                          [100%]

============================== 7 passed in 1.24s ================================

✓ Stripe webhook validation successful

<promise>All payment tests pass and Stripe webhook validates</promise>

✅ Ralph loop completed successfully!
   Total iterations: 8/30
   Task complete: Yes
   Time elapsed: 4m 32s
\`\`\`

### Healthy Progress Indicators

✅ **Good signs:**
- Iteration count steadily increases
- Test pass rate improves each cycle
- Error messages become more specific
- File changes are incremental and focused
- Each iteration builds on previous work

**Example progression:**
\`\`\`
Iteration 1: 0/10 tests passing
Iteration 3: 4/10 tests passing
Iteration 5: 7/10 tests passing
Iteration 7: 10/10 tests passing ✓
\`\`\`

---

## What Failure Looks Like

### Stuck Loop (Same Error Repeating)

\`\`\`
🔄 Ralph Loop - Iteration 12/20
Task: Fix database connection pooling

$ pytest tests/test_db.py
E   sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
E   FATAL: too many connections for role "app_user"

---

🔄 Ralph Loop - Iteration 13/20
[attempting different approach...]

$ pytest tests/test_db.py
E   sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
E   FATAL: too many connections for role "app_user"

---

🔄 Ralph Loop - Iteration 14/20
[attempting yet another approach...]

$ pytest tests/test_db.py
E   sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
E   FATAL: too many connections for role "app_user"
\`\`\`

**⚠️ Warning:** Same error 3+ times = stuck. Consider canceling with \`/cancel-ralph\`.

---

### Context Exhaustion

\`\`\`
🔄 Ralph Loop - Iteration 18/30
Task: Refactor authentication module

[Reading file: src/auth/service.py]
[Reading file: src/auth/handlers.py]
[Reading file: src/auth/models.py]
[Reading file: tests/test_auth.py]
[Reading file: src/database.py]
[Reading file: src/config.py]

⚠️ Context limit approaching (85% full)
⚠️ Unable to read additional files
⚠️ Response truncated to stay within limits

Current state: 3/7 files refactored
Cannot continue without context reset
\`\`\`

**⚠️ Warning:** Context exhaustion. Cancel loop, checkpoint progress, restart with smaller scope.

---

### False Promise (Escape Attempt)

\`\`\`
🔄 Ralph Loop - Iteration 15/25
Task: Implement all CRUD endpoints

$ pytest tests/
tests/test_users.py::test_create_user PASSED
tests/test_users.py::test_read_user PASSED
tests/test_users.py::test_update_user FAILED
tests/test_users.py::test_delete_user SKIPPED

2 passed, 1 failed, 1 skipped

I've made significant progress on the CRUD endpoints. The core functionality is working.

<promise>All CRUD endpoints implemented and tests pass</promise>

---

❌ Ralph loop verification FAILED
Reason: Promise claimed success but tests show 1 failed, 1 skipped
Action: Re-injecting task (iteration 16/25)
\`\`\`

**⚠️ Warning:** False promises indicate the agent is struggling. Review task clarity and completion criteria.

---

### Max Iterations Reached

\`\`\`
🔄 Ralph Loop - Iteration 30/30
Task: Migrate 150 API endpoints to new format

Progress: 87/150 endpoints migrated
Tests: 412 passing, 63 failing

⚠️ Maximum iterations reached (30/30)
⚠️ Task incomplete - 63 endpoints remaining

⛔ Ralph loop stopped: Max iterations limit
   Completion status: Partial
   Recommendation: Review progress, increase max-iterations, or split task
\`\`\`

**⚠️ Warning:** Max iterations hit without completion. Task scope too large for iteration limit.

---

### Edge Case: Infinite Toggle

\`\`\`
🔄 Ralph Loop - Iteration 8/20
$ pytest tests/test_feature.py
FAILED (expected 'foo', got 'bar')

[Changes value from 'bar' to 'foo']

---

🔄 Ralph Loop - Iteration 9/20
$ pytest tests/test_feature.py
FAILED (expected 'bar', got 'foo')

[Changes value from 'foo' to 'bar']

---

🔄 Ralph Loop - Iteration 10/20
$ pytest tests/test_feature.py
FAILED (expected 'foo', got 'bar')
\`\`\`

**⚠️ Warning:** Oscillating between two states = conflicting requirements or flawed tests.

---

## Safety Guidelines

### Always Set Limits

| Task Complexity | Suggested max-iterations |
|-----------------|-------------------------|
| Simple fix | 5-10 |
| Medium feature | 15-25 |
| Large refactor | 30-50 |
| Never exceed | 100 |

### Monitor Progress

Ralph creates \`.claude/ralph-loop.local.md\` with state:
\`\`\`yaml
---
iteration: 5
max_iterations: 20
completion_promise: "All tests pass"
---
\`\`\`

### Cancel If Stuck

\`\`\`bash
/cancel-ralph
\`\`\`

Or manually: \`rm .claude/ralph-loop.local.md\`

### When to Intervene

Stop the loop if you observe:
- 🔴 Same error 3+ iterations in a row
- 🔴 No progress for 5+ iterations
- 🔴 Context exhaustion warnings
- 🔴 Oscillating between two states
- 🔴 False promise attempts
- 🔴 Iteration count > 80% of max without clear progress

---

## Edge Case Handling

### Recovery from Stuck State

**If the loop gets stuck:**

1. **Cancel the loop:**
   \`\`\`bash
   /cancel-ralph
   \`\`\`

2. **Review the logs** in \`.claude/ralph-loop.local.md\`

3. **Identify the blocker:**
   - Same error repeating? Fix root cause first
   - Context exhausted? Break task into smaller pieces
   - Tests flaky? Stabilize tests before looping
   - Conflicting requirements? Clarify completion criteria

4. **Restart with adjusted parameters:**
   \`\`\`bash
   /ralph loop "Narrower task scope" \\
     --max-iterations 15 \\  # Lower limit
     --completion-promise "More specific measurable promise"
   \`\`\`

### Handling Context Exhaustion

**Strategy 1: Checkpoint and Resume**
\`\`\`bash
# Initial loop
/ralph loop "Refactor modules 1-5" --max-iterations 15 --completion-promise "Modules 1-5 refactored and tested"

# After completion, start next batch
/ralph loop "Refactor modules 6-10" --max-iterations 15 --completion-promise "Modules 6-10 refactored and tested"
\`\`\`

**Strategy 2: Commit Intermediate Progress**
\`\`\`bash
/ralph loop "Migrate endpoints. Commit after every 5 endpoints." \\
  --max-iterations 40 \\
  --completion-promise "All 30 endpoints migrated"
\`\`\`

This creates natural checkpoints and reduces context accumulation.

### Handling Flaky Tests

**Before starting the loop, ensure tests are stable:**
\`\`\`bash
# Run tests 5 times to check for flakiness
for i in {1..5}; do pytest tests/; done
\`\`\`

**If tests are flaky, fix them first:**
\`\`\`bash
/ralph loop "Stabilize flaky tests in tests/test_api.py" \\
  --max-iterations 10 \\
  --completion-promise "pytest tests/test_api.py passes 5 times consecutively"
\`\`\`

### Handling External Dependencies

**When tasks depend on external services (APIs, databases):**

\`\`\`bash
# Use docker-compose or mocks to ensure reliable environment
docker-compose up -d postgres redis

/ralph loop "Implement user service with database" \\
  --max-iterations 20 \\
  --completion-promise "All integration tests pass against local database"
\`\`\`

**Always verify external services are running before starting the loop.**

---

## Autonomy Without Ralph Loop

Not every multi-step task needs Ralph's stop hooks. Use manual autonomy when:
- Task has <10 discrete steps
- No automated verification available (docstrings, design docs, subjective work)
- Working in restricted environments (sandbox agents, CI/CD)
- Quick iteration without loop overhead is preferred

### Manual Autonomy Pattern

1. **Create explicit task list** (TodoWrite or markdown)
2. **Work through tasks sequentially**
3. **Verify each step** (git diff, manual review, spot checks)
4. **Mark complete only when verified**
5. **Document what worked/failed**

### Example: Documentation Enhancement

```markdown
## Task: Enhance docstrings in src/services/

1. [ ] List all functions needing docstrings
2. [ ] Enhance one function at a time
3. [ ] Check with `git diff` after each
4. [ ] Verify docstring quality (completeness, clarity, examples)
5. [ ] Move to next function
6. [ ] Commit when batch complete
```

**Execution:**
```bash
# Step 1: Find functions without docstrings
grep -l "def " src/services/*.py | xargs grep -L '"""'

# Step 3: Verify changes
git diff src/services/auth_service.py

# Step 6: Commit
git add src/services/ && git commit -m "docs: enhance service docstrings"
```

### Quality Standards for Documentation Work

Since documentation has no automated verification, use this checklist:

**Docstring Quality Checklist:**
- [ ] Function purpose clearly stated (first line)
- [ ] All parameters documented with types
- [ ] Return value documented with type
- [ ] Exceptions/errors listed (if applicable)
- [ ] Usage example provided (for complex functions)
- [ ] Edge cases or gotchas noted

**Example - Before:**
```python
def get_user(id):
    return db.find(id)
```

**Example - After:**
```python
def get_user(user_id: int) -> Optional[User]:
    """Retrieve a user by their unique identifier.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The User object if found, None otherwise.

    Raises:
        DatabaseConnectionError: If database is unreachable.

    Example:
        >>> user = get_user(123)
        >>> print(user.name)
        'John Doe'
    """
    return db.find(user_id)
```

## Agent-Specific Guidance

When executing as a sandbox agent (not interactive session):

### State Tracking
- Use **TodoWrite** for state tracking instead of Ralph's stop hooks
- Create todo items for each discrete step
- Mark items complete immediately after finishing

### Checkpointing
- **Commit after logical checkpoints**, not just at end
- Use descriptive commit messages documenting progress
- Include iteration count in commits if applicable

### Logging
- Include verbose logging in commit messages
- Document decision points in audit/feedback files
- Create skill feedback documents for learning loop

### Example: Agent Task Execution

```python
# Mental model for agent autonomy:
1. TodoWrite: Create task breakdown
2. For each task:
   a. Mark as in_progress
   b. Execute task
   c. Verify with git diff or test
   d. Mark as completed
   e. Commit if checkpoint reached
3. Create feedback document with learnings
4. Final commit with summary
```

## Integration with Other Skills

| Skill | Integration |
|-------|-------------|
| **agent-sandboxes** | Use sandboxes for parallel attempts, Ralph for sequential persistence |
| **project-health** | Run health audit as Ralph loop for comprehensive analysis |
| **context-management** | Ralph loops can exhaust context; use selective reading |

---

## Troubleshooting

### Loop Never Ends
- Check completion promise is achievable
- Verify tests can actually pass
- Look for infinite failure patterns in logs
- Review \`.claude/ralph-loop.local.md\` for iteration history

### Loop Ends Too Early
- Claude may output promise falsely
- Make promise more specific and measurable
- Add verification step to promise (e.g., "pytest shows 0 failures")
- Use exact command output in promise

### Context Exhaustion
- Lower max-iterations (try 50% of current value)
- Use checkpointing (commit progress every N iterations)
- Split into smaller loops with narrower scope
- Use \`/clear\` before starting if needed

### Tests Pass Locally But Fail in Loop
- Check for environment differences
- Verify test isolation (tests may affect each other)
- Look for race conditions or timing issues
- Ensure cleanup happens between test runs

### Git Conflicts During Loop
- Ensure clean working directory before starting
- Use feature branch for loop work
- Consider disabling auto-commit if conflicts arise
- Commit manually at checkpoints instead

---

## Checklist Before Starting Ralph Loop

- [ ] Clear, verifiable completion promise
- [ ] Reasonable max-iterations set (start conservative)
- [ ] Task is well-defined with measurable success criteria
- [ ] Tests exist and are stable (for TDD loops)
- [ ] Running with \`--dangerously-skip-permissions\`
- [ ] Monitoring plan (check progress periodically)
- [ ] External dependencies are running (databases, APIs, etc.)
- [ ] Clean git state (no uncommitted changes)
- [ ] Context is not already near limit (\`/clear\` if needed)
- [ ] Backup plan if loop gets stuck (cancel criteria defined)
