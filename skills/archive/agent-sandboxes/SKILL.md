---
name: agent-sandboxes
description: Run parallel Claude Code agents in isolated E2B cloud sandboxes. Use for multi-stream development tasks, comprehensive audits, or when context isolation is needed. Each agent can run Ralph loops for persistence.
---

# Agent Sandboxes (E2B + Claude Code)

Run parallel, isolated Claude Code agents in E2B cloud sandboxes. Each agent has its own context window and can run Ralph loops for persistent tasks.

## Skills Location

**Skills live in the repo at `skills/`** - not at `~/.claude/skills/`.

When an E2B agent clones CommandCenter, skills are available at:
```
./skills/
├── agent-sandboxes/SKILL.md   # This file
├── autonomy/SKILL.md
├── context-management/SKILL.md
├── infrastructure-decisions/SKILL.md
├── project-health/SKILL.md
└── repository-hygiene/SKILL.md
```

Agents should read skills from `./skills/<skill-name>/SKILL.md` relative to repo root.

## ⚠️ COMMON FAILURE MODES (Read First!)

These are the actual failures encountered. Check each before running:

### 1. CLI Syntax Error
```bash
# ❌ WRONG - there is no 'sandbox-fork' subcommand
uv run obox sandbox-fork https://github.com/...

# ✅ CORRECT - repo URL is first positional argument
uv run obox https://github.com/... -p prompt.md
```

### 2. Branch Name with `/` Breaks Logging
Branch names like `feature/skills-native` contain `/` which was interpreted as directory path in log filenames. **Fixed in code** - branches are now sanitized (`/` → `-`).

### 3. System Prompt Template Errors
The system prompt uses Python `.format()`. Any `{...}` in code blocks will be interpreted as placeholders.

```markdown
# ❌ WRONG - Python sees {GITHUB_TOKEN} as placeholder
git remote set-url origin https://${GITHUB_TOKEN}@github.com/...

# ✅ CORRECT - Double braces escape for literal output
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/...
```

Valid placeholders: `{repo_url}`, `{branch}`, `{fork_number}`, `{allowed_directories}`

### 4. Git Push Authentication
**The sandbox is isolated** - no SSH keys, no inherited env vars.

**THREE things must happen:**
1. Token in `.env` file
2. Token passed to sandbox via `env_vars` parameter (done in code)
3. Agent must run: `git remote set-url origin https://$GITHUB_TOKEN@github.com/owner/repo.git`

---

## When to Use

- **Multi-stream development**: Run 4 agents on different features simultaneously
- **Comprehensive audits**: 6 agents for security, performance, docs, tests, etc.
- **Context isolation**: Each agent gets fresh 200k context
- **Persistent parallel work**: Ralph loop in each sandbox

## Prerequisites & API Keys

### Required Keys Location

All keys should be in `~/.config/api-keys/.env.api-keys` (sourced by .zshrc):

```bash
# Check your keys
cat ~/.config/api-keys/.env.api-keys | grep -E "^(ANTHROPIC|E2B|GITHUB)"
```

Expected keys:
```bash
ANTHROPIC_API_KEY=sk-ant-...      # For Claude Code in sandboxes
E2B_API_KEY=e2b_...               # For E2B sandbox management
GITHUB_TOKEN=ghp_...              # For git push/PR operations (needs 'repo' scope)
```

**IMPORTANT**: Use classic PATs (`ghp_...`), NOT OAuth tokens (`gho_...`). OAuth tokens expire and cause push failures.

### Setup Working Directory

```bash
cd ~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows

# Create .env from your global keys
cat > .env << EOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
E2B_API_KEY=${E2B_API_KEY}
GITHUB_TOKEN=${GITHUB_TOKEN}
EOF

# Verify all three are set
cat .env
```

---

## CLI Usage

### Correct Syntax

```bash
cd ~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows

# ✅ CORRECT - repo URL is positional argument
uv run obox <repo_url> --prompt <prompt> [options]

# ❌ WRONG - no 'sandbox-fork' subcommand
uv run obox sandbox-fork <repo_url>  # THIS WILL FAIL
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--prompt` | `-p` | **Required.** Prompt text or path to .md file |
| `--branch` | `-b` | Git branch to checkout/create |
| `--forks` | `-f` | Number of parallel agents (default: 1) |
| `--model` | `-m` | Model: opus, sonnet, haiku (default: sonnet) |
| `--max-turns` | `-t` | Maximum conversation turns |

### Examples

```bash
# Single agent with inline prompt
uv run obox https://github.com/PerformanceSuite/CommandCenter \
  -p "Add tests for the auth module" \
  -b feature/auth-tests \
  -m sonnet

# Single agent with prompt file
uv run obox https://github.com/PerformanceSuite/CommandCenter \
  -p prompts/my-task.md \
  -b feature/my-task \
  -m sonnet

# Multiple parallel agents (each gets unique branch: feature/audit-1, feature/audit-2, etc.)
uv run obox https://github.com/PerformanceSuite/CommandCenter \
  -p "Audit the codebase and report findings" \
  -b feature/audit \
  -f 3 \
  -m sonnet

# With max turns limit
uv run obox https://github.com/PerformanceSuite/CommandCenter \
  -p prompts/big-task.md \
  -b feature/big-task \
  -m sonnet \
  -t 80
```

---

## Writing Task Prompts

### Template for Tasks That Push to GitHub

```markdown
# Task Title

## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

```bash
git remote set-url origin https://${GITHUB_TOKEN}@github.com/<owner>/<repo>.git
git remote -v  # Verify
```

**You MUST do this before attempting to push.**

---

## Context

<describe the context>

## Your Mission

<describe what to accomplish>

## Branch

Create and work on: `<branch-name>`

## Step-by-Step Implementation

### Step 1: ...

<detailed instructions>

### Step 2: ...

<detailed instructions>

## Verification

```bash
<commands to verify work>
```

## Commit Strategy

1. `type(scope): first commit message`
2. `type(scope): second commit message`

## Push and Create PR

```bash
# Ensure remote uses token (CRITICAL!)
git remote set-url origin https://${GITHUB_TOKEN}@github.com/<owner>/<repo>.git

# Push
git push -u origin <branch-name>
```

## Completion Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Branch pushed to GitHub
```

---

## Parallel Execution Patterns

### Running 4 Streams in Parallel (via Terminal)

```bash
# Create prompts directory
mkdir -p prompts/parallel-tasks

# Create prompt files for each stream
# prompts/parallel-tasks/01-stream-a.md
# prompts/parallel-tasks/02-stream-b.md
# etc.

# Launch in separate terminals (or use osascript)
# Terminal 1:
uv run obox https://github.com/org/repo -p prompts/parallel-tasks/01-stream-a.md -b feature/stream-a -m sonnet

# Terminal 2:
uv run obox https://github.com/org/repo -p prompts/parallel-tasks/02-stream-b.md -b feature/stream-b -m sonnet

# Terminal 3:
uv run obox https://github.com/org/repo -p prompts/parallel-tasks/03-stream-c.md -b feature/stream-c -m sonnet

# Terminal 4:
uv run obox https://github.com/org/repo -p prompts/parallel-tasks/04-stream-d.md -b feature/stream-d -m sonnet
```

### Launching via osascript (from Claude)

```applescript
tell application "Terminal"
    do script "cd /path/to/sandbox_workflows && source .venv/bin/activate && uv run obox https://github.com/org/repo -p prompts/task.md -b feature/branch -m sonnet"
end tell
```

---

## Ralph Loop Inside Sandboxes

Each sandbox agent can use Ralph for persistent tasks:

```markdown
## Workflow
Use Ralph loop for persistence:

/ralph loop "Implement feature X. Run tests after each change. Fix failures before proceeding." \
  --max-iterations 15 \
  --completion-promise "All tests pass"
```

---

## Logs & Debugging

### Log Location

```bash
ls sandbox_agent_working_dir/logs/

# Format: {branch}-fork-{N}-{timestamp}.log
# Also: stream-{a,b,c,d}.log if using tee
```

### Tail Logs in Real-Time

```bash
tail -f sandbox_agent_working_dir/logs/*.log
```

### Common Log Messages

| Message | Meaning |
|---------|---------|
| `could not read Username` | Git auth not configured - token not reaching sandbox |
| `Agent execution completed` | Success, check cost/tokens |
| `ERROR: Command exited with code 128` | Git operation failed |

---

## Troubleshooting
## Troubleshooting

### Scenario 1: Token Authentication Failure

**Symptom**: Push fails with "could not read Username for 'https://github.com'"

**Error Log**:
```
ERROR: Command exited with code 128
remote: Support for password authentication was removed on August 13, 2021.
fatal: could not read Username for 'https://github.com': No such device or address
```

**Root Cause**: One or more of these issues:
1. Token not in `.env` file
2. Token not passed to sandbox via `env_vars` parameter
3. Git remote URL not reconfigured to use token
4. Using OAuth token (`gho_*`) instead of classic PAT (`ghp_*`)

**Fix**:
```bash
# Step 1: Verify token exists in .env
grep GITHUB_TOKEN .env

# Step 2: Verify it's a classic PAT (starts with ghp_)
grep GITHUB_TOKEN .env | grep -o 'ghp_' && echo "✓ Classic PAT" || echo "✗ OAuth token (will expire!)"

# Step 3: Test token validity
TOKEN=$(grep GITHUB_TOKEN .env | cut -d= -f2)
curl -s -H "Authorization: token $TOKEN" https://api.github.com/user | jq -r '.login'
# Should return your GitHub username

# Step 4: Verify task prompt includes git auth instructions
grep -A2 "git remote set-url" prompts/your-task.md
# Should show: git remote set-url origin https://${GITHUB_TOKEN}@github.com/...
```

**Prevention**: Always include this in task prompts:
```markdown
## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

\`\`\`bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/<owner>/<repo>.git
git remote -v  # Verify
\`\`\`

**You MUST do this before attempting to push.**
```

---

### Scenario 2: E2B Sandbox Timeout

**Symptom**: Agent stops mid-task with "Sandbox connection lost" or "Timeout exceeded"

**Error Log**:
```
E2BError: Sandbox iwm9c1xn61n4xcabthrgz timed out after 1800s
Agent execution incomplete. Check logs for last successful operation.
```

**Root Cause**: 
- Default sandbox lifetime is 30 minutes (1800s)
- Long-running tasks (build, test suites, large file operations) exceed timeout
- Agent didn't complete or push before timeout

**Fix**:
```bash
# Option 1: Increase timeout in CLI (max 3600s = 1 hour)
uv run obox https://github.com/org/repo \
  -p prompts/long-task.md \
  -b feature/task \
  --timeout 3600

# Option 2: Break task into smaller subtasks (recommended)
# Create prompts/subtask-1.md, subtask-2.md, etc.
# Run sequentially or in parallel with shorter timeouts
```

**Diagnostic**:
```bash
# Check sandbox status
e2b sandbox list

# Review last log entries before timeout
tail -n 50 sandbox_agent_working_dir/logs/feature-task-fork-1-*.log

# Look for what operation was in progress
grep -E "(Executing|Running|Building)" sandbox_agent_working_dir/logs/*.log | tail -10
```

**Recovery**:
```bash
# If work was committed but not pushed:
# 1. Check sandbox (if still alive within grace period)
e2b sandbox connect <sandbox-id>
e2b sandbox exec <sandbox-id> "cd /home/user/repo && git log -1"

# 2. If sandbox dead, work is lost - re-run with higher timeout or smaller scope
```

**Prevention**:
- For tasks >30min, use `--timeout 3600`
- Break large tasks into smaller chunks
- Have agent commit frequently (every major step)
- Use Ralph loop with checkpoints

---

### Scenario 3: Agent Completes But Work Is Lost

**Symptom**: Agent reports "Task completed successfully" but no branch on GitHub

**Error Log**:
```
✓ Files written
✓ Tests pass
✓ Committed changes
✗ Push failed - sandbox timed out before push
Agent execution completed
```

**Root Cause**:
- Agent committed locally in sandbox
- Never pushed to remote (forgot, failed auth, or timed out)
- Sandbox expired - all local work destroyed

**Fix** (if caught early):
```bash
# Step 1: List running sandboxes
e2b sandbox list

# Step 2: If sandbox still alive, connect and push manually
SANDBOX_ID=$(e2b sandbox list | grep "feature-task" | awk '{print $1}')

# Step 3: Execute push command
e2b sandbox exec $SANDBOX_ID "cd /home/user/repo && \
  git remote set-url origin https://$GITHUB_TOKEN@github.com/org/repo.git && \
  git push -u origin feature-task"
```

**Recovery** (if sandbox dead):
```bash
# Work is lost. Re-run with explicit push instruction:
# Add to task prompt:
---
## Final Step: PUSH IMMEDIATELY

After committing, push RIGHT AWAY:

\`\`\`bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/org/repo.git
git push -u origin <branch-name>

# Verify push succeeded
git branch -vv | grep '<branch-name>'
# Should show [origin/<branch-name>]
\`\`\`
---
```

**Prevention**:
- Always include explicit push instructions in task prompts
- Have agent verify push success before reporting completion
- Use shorter tasks so completion happens before timeout
- Monitor logs in real-time: `tail -f sandbox_agent_working_dir/logs/*.log`

---

### Scenario 4: Context Exhaustion Mid-Task

**Symptom**: Agent becomes repetitive, forgets instructions, or makes errors

**Error Log**:
```
Turn 45/80: Agent attempting same operation for 3rd time
Turn 52/80: Agent asking for information already provided
Turn 60/80: Output quality degraded
```

**Root Cause**:
- Task too large for single context window (200k tokens)
- Agent re-reading large files repeatedly
- Circular logic or stuck in loop
- Context filled with error messages from failed attempts

**Diagnostic**:
```bash
# Count token usage from logs
grep "Token usage" sandbox_agent_working_dir/logs/feature-task-*.log | tail -20

# Look for repeated operations
grep -E "(Reading|Writing|Executing)" sandbox_agent_working_dir/logs/*.log | \
  awk '{print $NF}' | sort | uniq -c | sort -rn | head -10

# Check for error loops
grep -c "Error:" sandbox_agent_working_dir/logs/*.log
```

**Fix**:
```bash
# Option 1: Reduce prompt scope
# Split into Phase 1, Phase 2 prompts
# Run sequentially: uv run obox ... -p phase1.md, then phase2.md

# Option 2: Use Ralph loop with completion criteria
# In task prompt:
/ralph loop "Implement auth. Tests must pass." \
  --max-iterations 10 \
  --completion-promise "All auth tests pass"

# Option 3: Set lower max-turns to fail fast
uv run obox ... -t 30  # Fail at 30 turns instead of default 50
```

**Recovery**:
If agent is stuck mid-task:
```bash
# Kill the sandbox to stop wasting tokens
e2b sandbox kill <sandbox-id>

# Review what was accomplished
git clone https://github.com/org/repo -b feature-task /tmp/review
cd /tmp/review
git log  # See what commits made it

# Re-run with refined prompt addressing failure mode
```

**Prevention**:
- Keep prompts focused and scoped
- Provide clear completion criteria
- Use `--max-turns` to limit runaway executions
- Test prompts with smaller tasks first
- Monitor token usage in logs

---

### Scenario 5: Parallel Agent Conflicts

**Symptom**: Multiple agents trying to push to same branch or edit same files

**Error Log**:
```
# Agent 1:
✓ Pushed to feature/docs-update

# Agent 2 (seconds later):
✗ Push rejected - non-fast-forward
! [rejected] feature/docs-update -> feature/docs-update (fetch first)
```

**Root Cause**:
- Multiple agents given same branch name
- Parallel agents editing overlapping files
- Race condition on push operations

**Diagnostic**:
```bash
# Check which agents are running on which branches
grep "Checked out branch" sandbox_agent_working_dir/logs/*.log

# Check for push conflicts
grep -E "(rejected|non-fast-forward)" sandbox_agent_working_dir/logs/*.log

# List all active sandboxes
e2b sandbox list
```

**Fix**:
```bash
# Option 1: Use fork numbering (automatic when using --forks)
uv run obox https://github.com/org/repo \
  -p prompts/task.md \
  -b feature/docs \
  --forks 3
# Creates: feature/docs-1, feature/docs-2, feature/docs-3

# Option 2: Manual unique branches
uv run obox ... -b feature/docs-section-1
uv run obox ... -b feature/docs-section-2
uv run obox ... -b feature/docs-section-3

# Option 3: Sequential execution
uv run obox ... -b feature/docs  # Wait for completion
uv run obox ... -b feature/tests # Then run next
```

**Recovery**:
```bash
# For non-fast-forward pushes:
# 1. Identify which agent pushed first
grep "Successfully pushed" sandbox_agent_working_dir/logs/*.log

# 2. For losing agent, rebase and retry
e2b sandbox exec <sandbox-id-2> "cd /home/user/repo && \
  git fetch origin && \
  git rebase origin/feature/docs && \
  git push -u origin feature/docs"

# 3. Or push to different branch
e2b sandbox exec <sandbox-id-2> "cd /home/user/repo && \
  git checkout -b feature/docs-alt && \
  git push -u origin feature/docs-alt"
```

**Prevention**:
- Always use unique branch names per agent
- Use `--forks` flag for automatic numbering
- Design parallel tasks to work on separate files/modules
- Coordinate merge order in advance

---

### Scenario 6: System Prompt Template Placeholder Error

**Symptom**: Task prompt has shell variables that break Python `.format()`

**Error Log**:
```
KeyError: 'GITHUB_TOKEN'
Error rendering system prompt template
Task aborted before agent creation
```

**Root Cause**:
Task prompt contains `${GITHUB_TOKEN}` or `{VARIABLE}` which Python interprets as `.format()` placeholder.

**Example of Breaking Prompt**:
```markdown
git remote set-url origin https://${GITHUB_TOKEN}@github.com/org/repo.git
```

**Fix**:
Double the braces to escape them:
```markdown
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/org/repo.git
```

**Valid placeholders** (single braces OK):
- `{repo_url}`
- `{branch}`
- `{fork_number}`
- `{allowed_directories}`

**Diagnostic**:
```bash
# Check prompt file for unescaped braces
grep -E '\$\{[A-Z_]+\}' prompts/task.md
# If found, wrap in double braces: ${{VAR}}

# Validate by rendering template manually
python3 << 'EOF'
with open('prompts/task.md') as f:
    content = f.read()
    try:
        content.format(repo_url="test", branch="test", fork_number=1, allowed_directories="test")
        print("✓ Template valid")
    except KeyError as e:
        print(f"✗ Invalid placeholder: {e}")
EOF
```

**Prevention**:
- Use double braces for all shell variables: `${{VAR}}`
- Only use single braces for obox placeholders
- Test prompts with `python -c "open('prompt.md').read().format(...)"`

---

### Scenario 7: CLI Argument Parsing Error

**Symptom**: "Got unexpected extra argument" or "No such command 'sandbox-fork'"

**Error Log**:
```
Error: Got unexpected extra argument (sandbox-fork)
Usage: obox [OPTIONS] REPO_URL
```

**Root Cause**:
Using old/wrong CLI syntax. There is no `sandbox-fork` subcommand.

**Wrong**:
```bash
uv run obox sandbox-fork https://github.com/org/repo
```

**Correct**:
```bash
uv run obox https://github.com/org/repo -p "Task description"
```

**Diagnostic**:
```bash
# Check CLI help
uv run obox --help

# Verify you're using positional REPO_URL (no subcommand)
```

**Fix**:
```bash
# Remove 'sandbox-fork' from command
uv run obox https://github.com/PerformanceSuite/CommandCenter \
  --prompt prompts/task.md \
  --branch feature/task \
  --model sonnet
```

---

## Diagnostic Commands

### Pre-Flight Diagnostics

Run these before executing sandbox tasks:

```bash
# 1. Verify working directory
pwd
# Should be: ~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows

# 2. Verify dependencies installed
uv sync && echo "✓ Dependencies OK"

# 3. Check all API keys present
for key in ANTHROPIC_API_KEY E2B_API_KEY GITHUB_TOKEN; do
  grep -q "^${key}=" .env && echo "✓ $key present" || echo "✗ $key MISSING"
done

# 4. Validate GITHUB_TOKEN format (should be ghp_* not gho_*)
grep GITHUB_TOKEN .env | grep -o '^GITHUB_TOKEN=ghp_' && \
  echo "✓ Classic PAT" || echo "⚠ Check token type"

# 5. Test GITHUB_TOKEN works
TOKEN=$(grep GITHUB_TOKEN .env | cut -d= -f2)
curl -sf -H "Authorization: token $TOKEN" https://api.github.com/user > /dev/null && \
  echo "✓ Token valid" || echo "✗ Token invalid/expired"

# 6. Check E2B API key works
TOKEN=$(grep E2B_API_KEY .env | cut -d= -f2)
curl -sf -H "Authorization: Bearer $TOKEN" https://api.e2b.dev/sandboxes > /dev/null && \
  echo "✓ E2B key valid" || echo "✗ E2B key invalid"

# 7. Validate task prompt exists and is readable
test -f prompts/task.md && echo "✓ Prompt file exists" || echo "✗ Prompt file missing"

# 8. Check prompt for common issues
if test -f prompts/task.md; then
  grep -q '${{GITHUB_TOKEN}}' prompts/task.md && echo "✓ Token variable escaped" || \
    echo "⚠ Check token variable format"
fi
```

### Mid-Execution Diagnostics

Monitor running agents:

```bash
# 1. List active sandboxes
e2b sandbox list

# 2. Tail logs in real-time
tail -f sandbox_agent_working_dir/logs/*.log

# 3. Check token usage (watch for context exhaustion)
tail -n 100 sandbox_agent_working_dir/logs/*.log | grep "Token usage"

# 4. Count errors in logs
for log in sandbox_agent_working_dir/logs/*.log; do
  echo "$log: $(grep -c 'Error:' $log) errors"
done

# 5. Check agent progress (search for completion markers)
grep -E "(✓|✗|Success|Failed)" sandbox_agent_working_dir/logs/*.log | tail -20

# 6. Monitor git operations
grep -E "(git add|git commit|git push)" sandbox_agent_working_dir/logs/*.log | tail -20

# 7. Check for repeated operations (possible loop)
tail -n 50 sandbox_agent_working_dir/logs/*.log | \
  grep "Executing" | awk '{print $NF}' | sort | uniq -c | sort -rn
```

### Post-Execution Diagnostics

After agent completes:

```bash
# 1. Review completion status
grep "Agent execution completed" sandbox_agent_working_dir/logs/*.log

# 2. Check cost/token usage
grep -E "(Cost|tokens)" sandbox_agent_working_dir/logs/*.log | tail -10

# 3. Verify push succeeded
grep "Successfully pushed" sandbox_agent_working_dir/logs/*.log

# 4. Check for push failures
grep -E "(rejected|failed to push|could not read Username)" \
  sandbox_agent_working_dir/logs/*.log

# 5. Review commits made
git fetch origin
git log origin/feature-branch --oneline

# 6. Verify branch exists on remote
git ls-remote --heads origin | grep feature-branch

# 7. Check sandbox cleanup
e2b sandbox list | grep -c "feature-branch" || echo "✓ Sandboxes cleaned up"
```

---

## Log Analysis Guide

### Understanding Log Format

Logs are written to: `sandbox_agent_working_dir/logs/{branch}-fork-{N}-{timestamp}.log`

**Key sections to look for:**

1. **Initialization**:
```
Initializing sandbox...
✓ Sandbox created: iwm9c1xn61n4xcabthrgz
```

2. **Repository setup**:
```
Cloning repository...
✓ Repository cloned
Checked out branch: feature/task
```

3. **Agent execution**:
```
Turn 1/50: <agent action>
Token usage: 15234/200000
```

4. **Git operations**:
```
Executing: git add .
Executing: git commit -m "message"
Executing: git push -u origin feature/task
```

5. **Completion**:
```
Agent execution completed
Total cost: $1.23
```

### Reading Success Logs

**Example of successful execution:**
```
[2024-01-15 10:30:00] Initializing sandbox...
[2024-01-15 10:30:05] ✓ Sandbox created: iwm9c1xn61n4xcabthrgz
[2024-01-15 10:30:10] ✓ Repository cloned to /home/user/repo
[2024-01-15 10:30:12] ✓ Checked out branch: feature/docs
[2024-01-15 10:30:15] Turn 1/50: Reading existing documentation
[2024-01-15 10:30:20] Token usage: 5234/200000
[2024-01-15 10:32:45] Turn 5/50: Writing updated docs
[2024-01-15 10:33:10] ✓ Files written: 3 files
[2024-01-15 10:33:15] Executing: git add .
[2024-01-15 10:33:16] Executing: git commit -m "docs: update API documentation"
[2024-01-15 10:33:18] Executing: git remote set-url origin https://ghp_***@github.com/org/repo.git
[2024-01-15 10:33:20] Executing: git push -u origin feature/docs
[2024-01-15 10:33:25] ✓ Successfully pushed to origin/feature/docs
[2024-01-15 10:33:30] Agent execution completed
[2024-01-15 10:33:30] Total tokens: 45230 input, 12450 output
[2024-01-15 10:33:30] Total cost: $1.23
```

**Success indicators:**
- ✓ checkmarks for each major step
- `Successfully pushed to origin/`
- `Agent execution completed`
- Reasonable token usage (< 180k)
- Cost within expected range

### Reading Failure Logs

**Example of auth failure:**
```
[2024-01-15 10:30:00] Initializing sandbox...
[2024-01-15 10:30:05] ✓ Sandbox created: iwm9c1xn61n4xcabthrgz
[2024-01-15 10:35:10] Executing: git push -u origin feature/docs
[2024-01-15 10:35:15] ERROR: Command exited with code 128
[2024-01-15 10:35:15] STDERR: fatal: could not read Username for 'https://github.com'
[2024-01-15 10:35:20] ✗ Push failed
[2024-01-15 10:35:30] Agent execution completed (with errors)
```

**Failure indicators:**
- ✗ marks or ERROR messages
- Exit codes > 0
- `could not read Username`
- `rejected` or `non-fast-forward`
- `timed out` or connection errors

**Example of context exhaustion:**
```
[2024-01-15 10:45:00] Turn 35/50: Reading file X
[2024-01-15 10:45:10] Token usage: 145000/200000
[2024-01-15 10:46:00] Turn 36/50: Reading file X  # <-- Repeated action
[2024-01-15 10:46:10] Token usage: 165000/200000
[2024-01-15 10:47:00] Turn 37/50: Reading file X  # <-- Same again
[2024-01-15 10:47:10] Token usage: 185000/200000  # <-- Approaching limit
```

**Context exhaustion indicators:**
- Token usage > 150k
- Repeated identical operations
- Agent "forgetting" previous steps
- Degraded output quality

---

## Recovery Playbook

### Playbook 1: Recover from Failed Push (Sandbox Still Alive)

**When**: Agent completed work but push failed, sandbox still running

```bash
# Step 1: Find sandbox ID
e2b sandbox list | grep "feature-task"

# Step 2: Verify commits exist in sandbox
SANDBOX_ID=<from-step-1>
e2b sandbox exec $SANDBOX_ID "cd /home/user/repo && git log --oneline -5"

# Step 3: Configure git auth in sandbox
e2b sandbox exec $SANDBOX_ID "cd /home/user/repo && \
  git remote set-url origin https://$GITHUB_TOKEN@github.com/org/repo.git"

# Step 4: Push
e2b sandbox exec $SANDBOX_ID "cd /home/user/repo && \
  git push -u origin feature-task"

# Step 5: Verify
git fetch origin
git log origin/feature-task --oneline

# Step 6: Cleanup
e2b sandbox kill $SANDBOX_ID
```

### Playbook 2: Recover from Timeout (Work Lost)

**When**: Sandbox timed out before completion, all work lost

```bash
# Step 1: Review logs to see what was completed
grep -E "(✓|Completed)" sandbox_agent_working_dir/logs/feature-task-*.log

# Step 2: Assess if partial work was valuable
# If yes, document what was done and create refined prompt
# If no, simplify original task scope

# Step 3: Create refined prompt addressing timeout
cat > prompts/task-refined.md << 'EOF'
# Task (Refined - Reduced Scope)

## Context
Previous attempt timed out at step 3. This prompt covers steps 1-2 only.

## Your Mission
[Smaller, focused task]

## Time Estimate
Should complete in < 20 minutes

## Completion Criteria
- [ ] Step 1 done
- [ ] Step 2 done
- [ ] Committed and pushed
EOF

# Step 4: Re-run with higher timeout or smaller scope
uv run obox https://github.com/org/repo \
  -p prompts/task-refined.md \
  -b feature/task-v2 \
  --timeout 3600 \
  -m sonnet
```

### Playbook 3: Recover from Context Exhaustion

**When**: Agent stuck in loop or making repeated errors

```bash
# Step 1: Kill sandbox to stop token burn
SANDBOX_ID=$(e2b sandbox list | grep "feature-task" | awk '{print $1}')
e2b sandbox kill $SANDBOX_ID

# Step 2: Review what was accomplished
tail -n 200 sandbox_agent_working_dir/logs/feature-task-*.log > /tmp/review.txt
grep -E "(✓|✗|Turn)" /tmp/review.txt

# Step 3: Identify loop pattern
grep "Executing" /tmp/review.txt | tail -20

# Step 4: Create focused prompt avoiding the loop
cat > prompts/task-focused.md << 'EOF'
# Task (Focused)

## Context
Previous attempt got stuck in loop at [specific step].

## Your Mission
[More specific instructions]

## IMPORTANT
Do NOT read file X repeatedly. Read once, process, move on.

## Completion Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Push immediately after completing
EOF

# Step 5: Re-run with lower max-turns to fail fast if looping
uv run obox https://github.com/org/repo \
  -p prompts/task-focused.md \
  -b feature/task-focused \
  --max-turns 30 \
  -m sonnet
```

### Playbook 4: Recover from Parallel Agent Conflicts

**When**: Multiple agents pushed conflicting changes to branches

```bash
# Step 1: Identify which agents succeeded
grep "Successfully pushed" sandbox_agent_working_dir/logs/*.log

# Step 2: List all branches created
git fetch origin
git branch -r | grep "feature/task"

# Step 3: Review each branch
for branch in $(git branch -r | grep "feature/task"); do
  echo "=== $branch ==="
  git log $branch --oneline -5
done

# Step 4: Choose merge strategy
# Option A: Merge all branches sequentially
git checkout -b feature/task-combined
git merge origin/feature/task-1
git merge origin/feature/task-2
git merge origin/feature/task-3
git push origin feature/task-combined

# Option B: Keep branches separate and create PRs individually
gh pr create --base main --head feature/task-1 --title "Task 1"
gh pr create --base main --head feature/task-2 --title "Task 2"
gh pr create --base main --head feature/task-3 --title "Task 3"

# Option C: Cherry-pick specific commits
git checkout -b feature/task-final
git cherry-pick origin/feature/task-1~3..origin/feature/task-1
git cherry-pick origin/feature/task-2~2..origin/feature/task-2
git push origin feature/task-final
```

### Playbook 5: Recover from Prompt Template Error

**When**: Task aborted before agent creation due to template error

```bash
# Step 1: Identify problematic placeholder
python3 << 'EOF'
with open('prompts/task.md') as f:
    content = f.read()
    try:
        content.format(repo_url="test", branch="test", fork_number=1, allowed_directories="test")
        print("✓ Template valid")
    except KeyError as e:
        print(f"✗ Invalid placeholder: {e}")
EOF

# Step 2: Find and fix unescaped braces
# Search for ${VAR} patterns
grep -n '\$\{[A-Z_]+\}' prompts/task.md

# Step 3: Replace with double braces
sed -i '' 's/\${\([A-Z_]*\)}/\$\{\{\1\}\}/g' prompts/task.md

# Step 4: Verify fix
python3 << 'EOF'
with open('prompts/task.md') as f:
    content = f.read()
    content.format(repo_url="test", branch="test", fork_number=1, allowed_directories="test")
    print("✓ Template now valid")
EOF

# Step 5: Re-run
uv run obox https://github.com/org/repo \
  -p prompts/task.md \
  -b feature/task \
  -m sonnet
```

---

## Pre-Flight Checklist

Before running sandboxes, verify:

- [ ] **Working directory**: `cd tools/agent-sandboxes/apps/sandbox_workflows`
- [ ] **Dependencies**: `uv sync`
- [ ] **ANTHROPIC_API_KEY** in `.env`
- [ ] **E2B_API_KEY** in `.env`
- [ ] **GITHUB_TOKEN** in `.env` (classic PAT with 'repo' scope)
- [ ] **Token works**: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user`
- [ ] **Task prompt includes git auth instructions** (if pushing)
- [ ] **CLI syntax**: `uv run obox <url> -p <prompt>` (no subcommand!)

---

## Cost Tracking

obox reports per-fork costs after completion:
- Input/output tokens
- Cost per agent
- Total run cost

**Typical costs:**
- Simple task (1 agent, 30 turns): ~$0.50-1.00
- Medium task (1 agent, 60 turns): ~$1.00-2.00
- Complex task (1 agent, 100 turns): ~$2.00-4.00
- Parallel assessment (4 agents): ~$4.00-10.00

Review costs before running large parallel jobs.

---

## Files Reference

| File | Purpose |
|------|---------|
| `.env` | API keys (ANTHROPIC, E2B, GITHUB) |
| `src/main.py` | CLI entry point |
| `src/commands/sandbox_fork.py` | Command implementation |
| `src/modules/agents.py` | Agent creation and execution |
| `src/modules/constants.py` | Configuration constants |
| `src/prompts/sandbox_fork_agent_system_prompt.md` | System prompt template |
| `sandbox_agent_working_dir/logs/` | Execution logs |
| `prompts/` | Task prompt files |
