---
status: active
name: context-management
description: Use proactively throughout sessions to maintain context under 50% capacity
  (100k tokens) via incremental cleanup, preventing expensive /compact operations
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
# Context Management Skill

**Goal**: Keep context usage under 50% capacity (100k/200k tokens) through continuous, non-disruptive optimization.

## Quick Decision Flowchart

```
┌─────────────────────────────────────────────────────────────────┐
│              START: Check Token Usage in System Reminder        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │  Calculate Usage % │
                    │  (tokens/200000)   │
                    └────────┬───────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌─────────┐       ┌─────────┐       ┌──────────┐
    │  0-40%  │       │ 40-60%  │       │  60%+    │
    │ Healthy │       │ Warning │       │ Critical │
    └────┬────┘       └────┬────┘       └────┬─────┘
         │                 │                  │
         ▼                 ▼                  ▼
    ┌─────────────┐  ┌──────────────┐  ┌────────────────┐
    │ Continue    │  │ Enable       │  │ Aggressive     │
    │ Normally    │  │ Optimization │  │ Cleanup        │
    │             │  │              │  │                │
    │ • Full      │  │ • Disable    │  │ • Thinking OFF │
    │   thinking  │  │   thinking   │  │ • Summarize    │
    │ • Normal    │  │ • Selective  │  │   everything   │
    │   reads     │  │   file reads │  │ • Filter all   │
    │             │  │ • Filter     │  │   outputs      │
    │             │  │   outputs    │  │ • Prune memory │
    └─────────────┘  └──────────────┘  └────────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │   80%+ ?     │
                                          └──────┬───────┘
                                                 │
                                        ┌────────┴────────┐
                                        │                 │
                                        ▼                 ▼
                                   ┌────────┐      ┌──────────┐
                                   │  YES   │      │    NO    │
                                   └────┬───┘      └──────────┘
                                        │
                                        ▼
                            ┌───────────────────────┐
                            │  EMERGENCY PROTOCOL   │
                            │                       │
                            │ 1. Complete task      │
                            │ 2. Commit changes     │
                            │ 3. Update memory      │
                            │ 4. Suggest /compact   │
                            └───────────────────────┘
```

## Quick Reference Card

| Scenario | Token Range | Strategy | Expected Savings | Action |
|----------|-------------|----------|------------------|--------|
| **Session Start** | 10-20k | MCP optimization | 15-25k tokens | Auto-disable unused MCPs |
| **Simple Task** | Any | Thinking suppression | 20-30% per response | \`<thinking_mode>disabled</thinking_mode>\` |
| **Large File Read** | Any | Selective reading | 50-80% per file | Use grep + offset/limit |
| **Command Output** | Any | Output filtering | 60-90% per command | Pipe to head/grep |
| **Task Complete** | 40k+ | Summarization | 10-15% | Summary instead of full output |
| **Mid-Session** | 80-100k | Memory pruning | 10-15k tokens | Clean old session entries |
| **Critical (60%+)** | 120k+ | Aggressive mode | 30-40% | All strategies combined |
| **Emergency (80%+)** | 160k+ | Compaction | Reset to ~10k | Save work + /compact |

## MANDATORY INVOCATION

**This skill is invoked automatically by \`/start\` command.**

You MUST follow its practices throughout the entire session:
- Thinking mode disabled by default (only enable for complex reasoning)
- Use \`gh\` CLI instead of GitHub MCP
- Selective file reading with offset/limit
- Filter command outputs with head/tail/grep

**DO NOT SKIP THESE PRACTICES** - they are mandatory, not optional.

## When to Use This Skill

**Proactive (Best):**
- At the start of every session (after /start) - AUTOMATICALLY INVOKED
- After completing major tasks (e.g., file writes, commits)
- Every 10-15 minutes during active development
- Before reading large files or generating long outputs

**Reactive (Fallback):**
- When system reminder shows >80k tokens
- When you notice slower responses
- Before complex tasks that will generate significant output

## Context Monitoring Protocol

### 1. Check Current Usage

When you see system reminders like:
\`\`\`
Token usage: 115584/200000; 84416 remaining
\`\`\`

Calculate percentage:
- **Current**: 115584 / 200000 = 58% ⚠️
- **Threshold**: 50% = 100k tokens

### 2. Alert Thresholds

| Usage | Status | Action |
|-------|--------|--------|
| 0-40% | ✅ Healthy | Continue normally |
| 40-50% | 🟡 Caution | Begin incremental cleanup |
| 50-60% | 🟠 Warning | Active cleanup + notifications |
| 60-80% | 🔴 Critical | Aggressive cleanup required |
| 80%+ | 🚨 Emergency | Immediate compaction |

### 3. Communicate Status

When threshold exceeded, inform user:

\`\`\`
🟡 Context at 45% (90k/200k) - Starting incremental cleanup
🟠 Context at 55% (110k/200k) - Active cleanup in progress
🔴 Context at 65% (130k/200k) - Aggressive cleanup needed
🚨 Context at 85% (170k/200k) - Emergency compaction required
\`\`\`

## Incremental Cleanup Strategies

### Strategy 0: MCP Server Optimization (Automatic on /start, -15-25k tokens)

**When**: Automatically during \`/start\` command

**Problem**: MCP servers consume massive context even when unused:
- GitHub MCP: ~18k tokens (26 tools)
- Puppeteer MCP: ~4.7k tokens
- Brave Search MCP: ~1.4k tokens
- IDE MCP: ~1.3k tokens

**Action**: Autonomously disable unused MCPs based on project type

**Before/After Example**:
\`\`\`
Before: All MCPs loaded
- Token usage: 25,400 tokens (system + tools)
- 4 MCP servers active
- 40+ tools in context

After: Optimized for backend project
- Token usage: 6,800 tokens (system only)
- 1 MCP server active (GitHub structure only, use gh CLI)
- 6 tools in context

Savings: 18,600 tokens (73% reduction in overhead)
\`\`\`

**Workflow**:
1. Read \`~/.claude/mcp.json\`
2. Detect project type (backend/frontend/fullstack/etc)
3. Identify unused MCPs:
   - **Always disable**: brave-search (redundant with WebSearch)
   - **Backend projects**: Disable puppeteer, ide (unless Jupyter notebooks present)
   - **Frontend projects**: Keep all (may need browser automation)
   - **GitHub**: Always keep enabled (but use \`gh\` CLI via Bash instead of MCP tools)
4. Comment out unused MCP entries
5. Report optimization results

**Implementation**: Automatically runs during \`/start\`, reports results like:
\`\`\`
🔧 MCP Optimization: Disabled 2 unused servers (saves ~6.1k tokens)
  - brave-search: Redundant with WebSearch
  - puppeteer: Not needed for backend work
\`\`\`

**Note**: Use \`gh\` CLI via Bash instead of GitHub MCP tools to save an additional ~18k tokens per session (even though GitHub MCP stays enabled for structure).

### Strategy 1: Thinking Suppression (Instant, -20-30%)

**When**: Disable thinking mode by default. Only enable for complex tasks.

**Disable thinking for**:
- Executing clear plans (step-by-step implementation)
- Simple file operations (read, write, edit)
- Running tests or commands
- Code lookups or searches
- Following established patterns

**Enable thinking ONLY for**:
- Brainstorming or design decisions
- Reviewing complex plans for issues
- Debugging ambiguous errors
- Architecture or approach selection
- Trade-off analysis

**Action**: Add at start of response:
\`\`\`markdown
<thinking_mode>disabled</thinking_mode>
\`\`\`

**Before/After Example**:

\`\`\`
Before: Response with thinking enabled
┌─────────────────────────────────────────────┐
│ <thinking>                                  │
│ The user wants to update the config file.   │
│ I should:                                   │
│ 1. Read the current file                   │
│ 2. Identify the section to modify          │
│ 3. Make the changes                        │
│ 4. Write it back                           │
│ This is straightforward...                 │
│ </thinking>                                │
│                                            │
│ I'll update the configuration file now.    │
│ [tool calls and response]                  │
└─────────────────────────────────────────────┘
Total: ~3,500 tokens

After: Response with thinking disabled
┌─────────────────────────────────────────────┐
│ <thinking_mode>disabled</thinking_mode>     │
│                                            │
│ I'll update the configuration file now.    │
│ [tool calls and response]                  │
└─────────────────────────────────────────────┘
Total: ~1,200 tokens

Savings: 2,300 tokens (66% reduction per response)
Over 10 responses: 23,000 tokens saved (11.5% of total budget)
\`\`\`

**Impact**:
- Reduces token usage by 20-30% immediately
- No quality loss for straightforward tasks
- Re-enable when needed: \`<thinking_mode>enabled</thinking_mode>\`

**Example**:
\`\`\`markdown
<thinking_mode>disabled</thinking_mode>

Executing Task 3: Update config file...
\`\`\`

### Strategy 2: Output Summarization (Fast, -10-15%)

**When**: After completing discrete tasks

**Action**: Instead of showing full tool outputs, summarize:

**Before/After Example**:

\`\`\`
Before: Full output quoted
┌─────────────────────────────────────────────┐
│ Read the configuration file:               │
│                                            │
│ <file contents - 500 lines>                │
│ [entire file quoted]                       │
│ </file contents>                           │
│                                            │
│ I've read the entire file. Let me now...   │
└─────────────────────────────────────────────┘
Total: ~8,200 tokens

After: Summarized output
┌─────────────────────────────────────────────┐
│ Read config.py (500 lines)                 │
│ Found 3 relevant sections:                 │
│ - Database config (lines 45-67)            │
│ - API settings (lines 120-145)             │
│ - Cache config (lines 230-256)             │
│                                            │
│ Proceeding with update...                  │
└─────────────────────────────────────────────┘
Total: ~1,100 tokens

Savings: 7,100 tokens (87% reduction per file operation)
\`\`\`

❌ **Don't** (wasteful):
\`\`\`
<file contents - 500 lines>
I've read the entire file. Let me now...
\`\`\`

✅ **Do** (efficient):
\`\`\`
Read config.py (500 lines) - found 3 relevant sections
Proceeding with update...
\`\`\`

### Strategy 3: Selective File Reading (Moderate, -15-25%)

**When**: Before reading files

**Actions**:
1. Use \`offset\` and \`limit\` parameters when possible
2. Grep/search before full reads
3. Read only changed sections for updates

**Before/After Example**:

\`\`\`
Before: Full file read
┌─────────────────────────────────────────────┐
│ Read(file_path="app/models/user.py")       │
│ → Returns entire file (850 lines)          │
│                                            │
│ Token usage: 12,400 tokens                 │
└─────────────────────────────────────────────┘

After: Targeted read with grep + offset/limit
┌─────────────────────────────────────────────┐
│ Grep(pattern="class User", path="app/      │
│      models/user.py")                      │
│ → Found at line 145                        │
│                                            │
│ Read(file_path="app/models/user.py",      │
│      offset=145, limit=50)                │
│ → Returns only relevant class (50 lines)   │
│                                            │
│ Token usage: 1,800 tokens                  │
└─────────────────────────────────────────────┘

Savings: 10,600 tokens (85% reduction per large file)
\`\`\`

❌ **Don't**:
\`\`\`python
Read(file_path="large_file.py")  # Reads entire file
\`\`\`

✅ **Do**:
\`\`\`python
Grep(pattern="class MyClass", path="large_file.py")  # Find location first
Read(file_path="large_file.py", offset=100, limit=50)  # Read targeted section
\`\`\`

### Strategy 4: Tool Output Filtering (Fast, -5-10%)

**When**: Running commands with verbose output

**Actions**:
1. Pipe to \`head\` or \`tail\` for previews
2. Use \`grep\` to filter relevant lines
3. Suppress unnecessary output

**Before/After Example**:

\`\`\`
Before: Full verbose test output
┌─────────────────────────────────────────────┐
│ $ pytest tests/ -v                         │
│                                            │
│ tests/test_auth.py::test_login PASSED     │
│ tests/test_auth.py::test_logout PASSED    │
│ tests/test_api.py::test_get_user PASSED   │
│ [... 200 more test lines ...]             │
│ tests/test_db.py::test_query PASSED       │
│                                            │
│ ========== 247 passed in 4.32s ==========  │
│                                            │
│ Token usage: 6,800 tokens                  │
└─────────────────────────────────────────────┘

After: Filtered output
┌─────────────────────────────────────────────┐
│ $ pytest tests/ -v 2>&1 | grep -E         │
│   "PASSED|FAILED|ERROR" | head -20         │
│                                            │
│ tests/test_auth.py::test_login PASSED     │
│ tests/test_auth.py::test_logout PASSED    │
│ [... 15 more lines ...]                   │
│ tests/test_api.py::test_update PASSED     │
│                                            │
│ $ pytest tests/ -v 2>&1 | tail -3         │
│ ========== 247 passed in 4.32s ==========  │
│                                            │
│ Token usage: 950 tokens                    │
└─────────────────────────────────────────────┘

Savings: 5,850 tokens (86% reduction per test run)
\`\`\`

❌ **Don't**:
\`\`\`bash
pytest tests/ -v  # Full verbose output
\`\`\`

✅ **Do**:
\`\`\`bash
pytest tests/ -v 2>&1 | grep -E "PASSED|FAILED|ERROR" | head -20
\`\`\`

### Strategy 5: Memory File Optimization (Moderate, -10-15%)

**When**: At task completion or every 30 minutes

**Actions**:
1. Remove outdated session entries from \`.claude/memory.md\`
2. Consolidate repetitive information
3. Move details to session logs instead of memory

**Before/After Example**:

\`\`\`
Before: Verbose memory with full details
┌─────────────────────────────────────────────┐
│ ## Session: 2025-10-20                     │
│ Started: 9:00 AM                           │
│ Work: Implemented user authentication      │
│ - Created login endpoint                   │
│ - Added JWT token generation               │
│ - Implemented token validation middleware  │
│ - Added refresh token rotation             │
│ - Created logout endpoint                  │
│ Status: Completed                          │
│ Next: Start working on authorization       │
│                                            │
│ ## Session: 2025-10-21                     │
│ [... similar verbose details ...]          │
│                                            │
│ ## Session: 2025-10-22                     │
│ [... similar verbose details ...]          │
│                                            │
│ Token usage: 14,200 tokens                 │
└─────────────────────────────────────────────┘

After: Optimized memory with references
┌─────────────────────────────────────────────┐
│ ## Session: 2025-10-26 (LATEST)            │
│ Work: Completed RAG service rewrite        │
│ Next: Dagger integration                   │
│ Details: .claude/logs/sessions/            │
│          2025-10-26_203915.md              │
│                                            │
│ ## Session: 2025-10-25                     │
│ Work: API optimization                     │
│ Details: .claude/logs/sessions/            │
│          2025-10-25_143022.md              │
│                                            │
│ Token usage: 1,800 tokens                  │
└─────────────────────────────────────────────┘

Savings: 12,400 tokens (87% reduction in memory overhead)
\`\`\`

**Example**:
\`\`\`markdown
## Session: 2025-10-26 (LATEST)
Work: Completed RAG service rewrite
Next: Dagger integration
Details: See .claude/logs/sessions/2025-10-26_203915.md
\`\`\`

### Strategy 6: Codebase Survey (For Multi-File Reviews)

**When**: Reviewing multiple files to identify patterns (e.g., router audit, service review)

**Problem**: Reading every file fully exhausts context before completing the review.

**Actions**:
1. Get inventory: `ls -la`, `wc -l *`, `grep -c "pattern" *`
2. Sample strategically: Read 20-30% of files fully, grep-sample remainder
3. Identify patterns: Common imports, naming conventions, structures
4. Deep-dive selectively: Full read only for unique/critical files
5. Document as you go: Write summaries incrementally

**Token Savings**: 40-60% for large multi-file reviews

**Example - Reviewing 29 Router Files:**
```bash
# Step 1: Get inventory
ls backend/app/routers/*.py | wc -l  # 29 files
wc -l backend/app/routers/*.py | sort -rn | head -5  # Find largest

# Step 2: Sample endpoints without full reads
grep -h "^@router\." backend/app/routers/*.py | wc -l  # 200+ endpoints

# Step 3: Full read key files only (20-30%)
# Read: auth.py, projects.py, graph.py, batch.py (critical)
# Grep-sample: remaining 25 files

# Step 4: Cross-file pattern detection
grep -r "from.*services" backend/app/routers/ | cut -d: -f2 | sort | uniq -c

# Result: 60k tokens used vs 140k estimated (57% savings)
```

### Strategy 7: Strategic Deep-Dive Criteria

**When**: Deciding whether to read a file fully or grep-sample it.

**Full Read If:**
- Core functionality or critical path
- Complex business logic
- Security-sensitive (auth, payments)
- File you need to modify
- Unique patterns not seen in other files

**Grep-Sample If:**
- Similar to other files already read
- Boilerplate or standard CRUD
- Large file (>500 lines) for quick overview
- Pattern already understood from other examples

**Rule of Thumb**: Read 20-30% of files fully, sample 70-80%

**Example Decision Tree:**
```
File: backend/app/routers/users.py (400 lines)
├── Is it critical path? → Read auth.py, projects.py
├── Does it follow patterns from files already read? → Grep-sample
├── Am I modifying it? → Full read
└── Is it boilerplate CRUD? → Grep endpoints only
```

### Strategy 8: Diminishing Returns Guidance

**When**: Deciding when to stop exploring and start summarizing

**Stopping Criteria for Large Reviews:**
- **Pattern clarity**: Can you describe the architecture confidently?
- **Coverage**: Have you examined 20-30% of code deeply?
- **Uniqueness**: Are new files showing new patterns or repeating existing?
- **Time**: After 30 min exploration, evaluate if additional reads add value

**Signs You Have Enough:**
- You can predict file contents before reading
- Same patterns appearing across multiple files
- No new concepts in last 3-5 files examined
- Confident you understand the architecture

**Signs You Need More:**
- Can't explain how pieces connect
- New patterns still emerging
- Critical files not yet examined
- Uncertainty about key functionality

### Strategy 9: Output Efficiency (Documentation Writing)

**When**: Creating large reports, summaries, or documentation

**Actions**:
- Write directly to files (not in chat) for long documents
- Use tables and lists (more compact than prose)
- Reference line numbers instead of code quotes
- Group related items to reduce repetition

**Before/After Example**:
```
Before: Full code quotes in response
┌─────────────────────────────────────────────┐
│ Here's the authentication implementation:   │
│                                             │
│ ```python                                   │
│ def login(email: str, password: str):       │
│     user = get_user_by_email(email)         │
│     if not user:                            │
│         raise HTTPException(404)            │
│     if not verify_password(password, ...):  │
│         raise HTTPException(401)            │
│     return create_token(user)               │
│ ```                                         │
│                                             │
│ Token usage: 2,400 tokens                   │
└─────────────────────────────────────────────┘

After: Line references
┌─────────────────────────────────────────────┐
│ Authentication implementation:              │
│ - Login: auth.py:45-67 (validates, tokens) │
│ - Refresh: auth.py:70-85 (JWT rotation)    │
│ - Logout: auth.py:88-95 (client-side)      │
│                                             │
│ Token usage: 350 tokens                     │
└─────────────────────────────────────────────┘

Savings: 2,050 tokens (85% reduction per reference)
```

### Strategy 10: Cross-File Analysis Commands

**When**: Finding patterns across multiple files without reading each fully

```bash
# Count endpoints per router file
for file in backend/app/routers/*.py; do
  echo "$(basename $file): $(grep -c '^@router\.' $file 2>/dev/null || echo 0)"
done

# List all unique HTTP methods used
grep -h '^@router\.' backend/app/routers/*.py | \
  sed 's/@router\.\([^(]*\).*/\1/' | sort -u

# Find common imports across services
grep -h "^from" backend/app/services/*.py | sort | uniq -c | sort -rn | head -10

# Detect file size distribution
find backend/app/routers -name "*.py" -exec wc -l {} + | sort -rn | head -10

# Check for patterns indicating complexity
grep -c "async def" backend/app/routers/*.py | sort -t: -k2 -rn | head -5
```

**Token Savings**: These commands give you architectural understanding at ~100-500 tokens vs 10-50k tokens for reading all files.

### Strategy 11: Conversation Pruning (Aggressive, -30-40%)

**When**: Critical threshold (60%+)

**Action**: Suggest to user:
\`\`\`
🔴 Context at 65% - Recommend conversation pruning:

Option 1: Continue with current task (5-10 min remaining)
Option 2: Complete task, then use /compact to reset context
Option 3: Start new session (save work first)

Current task will complete in ~X messages. Proceed?
\`\`\`

## Real Session Example: Optimization in Action

\`\`\`
Session Start: 10:00 AM
Initial tokens: 8,200 (system + tools)

──────────────────────────────────────────────────────────────

10:15 AM - After Reading 3 Files
Token usage: 32,400/200000 (16%)
✅ Status: Healthy

Response:
"Read 3 configuration files, identified settings to update"
[No optimization needed yet]

──────────────────────────────────────────────────────────────

10:35 AM - After Running Tests
Token usage: 78,600/200000 (39%)
✅ Status: Healthy, approaching caution

Response (normal):
"Tests passing. Proceeding with next feature..."

──────────────────────────────────────────────────────────────

10:50 AM - Multiple File Operations
Token usage: 92,800/200000 (46%)
🟡 Status: CAUTION - Begin optimization

Agent response:
"🟡 Context at 46% (92k/200k) - Starting incremental cleanup"

Optimizations enabled:
✓ Thinking mode: disabled for routine tasks
✓ File reading: using grep + offset/limit
✓ Command output: filtered with head/grep

Response example:
<thinking_mode>disabled</thinking_mode>

Grep found DatabaseConfig at line 245.
Reading lines 245-295 (50 lines).
Updated cache_timeout setting.

[Instead of quoting full 850-line file]

──────────────────────────────────────────────────────────────

11:10 AM - Continued Development
Token usage: 104,200/200000 (52%)
🟠 Status: WARNING - Active cleanup

Agent response:
"🟠 Context at 52% (104k/200k) - Active cleanup in progress"

Additional optimizations:
✓ Memory file: pruned old sessions (saved 8.2k tokens)
✓ Output: summaries only, no full quotes
✓ Tests: filtered to show only failures + summary

Response example:
<thinking_mode>disabled</thinking_mode>

Ran pytest (247 tests) → All passed in 4.32s
Updated API endpoint - changes committed.

──────────────────────────────────────────────────────────────

11:25 AM - Task Completion
Token usage: 118,400/200000 (59%)
🟠 Status: WARNING - Task nearly complete

Agent response:
"🟠 Context at 59% (118k/200k)

Task complete! Recommend:
1. Commit all work ✅
2. Update memory ✅
3. Start fresh session for next major feature

Type /end to close this session cleanly."

──────────────────────────────────────────────────────────────

Session Summary:
Duration: 1 hour 25 minutes
Work completed:
  - Updated 12 files
  - Added 3 new features
  - Ran test suite 5 times
  - Made 4 commits

Context management:
  - Started: 8.2k tokens (4%)
  - Ended: 118.4k tokens (59%)
  - Peak optimization: Saved ~35k tokens through strategies
  - Without optimization: Would have hit 153k tokens (76%)
    → Emergency compaction required
  - With optimization: Completed full session comfortably

Result: ✅ Successful session without disruption
\`\`\`

## Continuous Background Optimization

### Every Response Checklist

Before generating each response:

1. ☐ Check if system reminder shows token usage
2. ☐ If >40%, enable thinking_mode=disabled
3. ☐ Summarize instead of quoting full outputs
4. ☐ Use selective file reading
5. ☐ Filter tool outputs to essentials

### After Each Major Task

After file writes, commits, or task completion:

1. ☐ Note tokens saved via optimization
2. ☐ Update user if crossing threshold
3. ☐ Clean memory file if >300 lines
4. ☐ Compress session logs

## Prevention Best Practices

### File Operations

**Reading**:
- Use Grep before Read to locate sections
- Use offset/limit for large files
- Read only what's needed for the task

**Writing**:
- Don't re-read files you just wrote
- Trust Write/Edit tool success messages
- Avoid unnecessary verification reads

### Tool Selection: Use \`gh\` CLI Instead of GitHub MCP

**GitHub MCP Cost**: 26 tools × ~700 tokens = ~18k tokens loaded every session

**Alternative**: \`gh\` CLI via Bash tool (0 token overhead)

**Before/After Example**:

\`\`\`
Before: Using GitHub MCP
┌─────────────────────────────────────────────┐
│ Session startup:                           │
│ - Load 26 GitHub MCP tools                 │
│ - Tool definitions: ~18,000 tokens         │
│                                            │
│ Create PR:                                 │
│ mcp__github__create_pull_request(...)      │
│                                            │
│ Total overhead: 18,000 tokens (9% budget)  │
└─────────────────────────────────────────────┘

After: Using gh CLI via Bash
┌─────────────────────────────────────────────┐
│ Session startup:                           │
│ - No additional tools loaded               │
│ - Tool definitions: 0 tokens               │
│                                            │
│ Create PR:                                 │
│ gh pr create --title "feat: Add feature"  │
│   --body "Description"                     │
│                                            │
│ Total overhead: 0 tokens                   │
│                                            │
│ Savings: 18,000 tokens (9% of total       │
│          budget freed for actual work)     │
└─────────────────────────────────────────────┘
\`\`\`

✅ **Do** (0 MCP tokens):
\`\`\`bash
# Create PR
gh pr create --title "feat: Add feature" --body "Description"

# List issues
gh issue list --label bug --state open

# Get PR status
gh pr view 123 --json state,checks

# Create branch
gh repo clone owner/repo && git checkout -b feature

# Merge PR
gh pr merge 123 --squash
\`\`\`

❌ **Don't** (loads 26 tools, 18k tokens):
\`\`\`python
mcp__github__create_pull_request(...)  # Wastes tokens
mcp__github__list_issues(...)
mcp__github__get_pull_request_status(...)
\`\`\`

**When MCP is Better**:
- Rare cases where structured JSON output is critical
- Multi-file operations that \`gh\` doesn't support well

**Token Savings**: ~18k tokens (9% of budget) per session

### Command Execution

**Bash**:
- Pipe to \`head -20\` for previews
- Use \`grep\` to filter output
- Combine related commands (fewer tool calls)

**Tests**:
- Run specific tests, not full suites
- Filter output to failures only
- Use \`-q\` (quiet) mode when appropriate

### Communication

**Explanations**:
- Be concise but clear
- Use bullet points over paragraphs
- Save detailed docs to files, not responses

**Code Examples**:
- Show diffs, not full files
- Use "..." to indicate omitted sections
- Reference line numbers instead of quoting

## Emergency Compaction Protocol

### When: 80%+ Usage

**Immediate Actions**:

1. **Complete Current Task** (if <5 min):
   \`\`\`
   🚨 Context at 85% - Completing current task then compacting
   \`\`\`

2. **Save State**:
   - Commit all changes
   - Update memory.md with progress
   - Note next steps clearly

3. **Inform User**:
   \`\`\`
   🚨 Emergency: Context at 85% (170k/200k)

   Action: Use /compact to reset conversation

   Progress saved:
   - All changes committed
   - Memory updated with next steps
   - Ready to continue after compaction
   \`\`\`

4. **User Decision**:
   - Wait for user to run \`/compact\`
   - OR continue with extreme caution (thinking disabled, minimal output)

## Context Estimation (When No System Reminder)

**Rough estimates**:
- Average response: ~1-2k tokens
- File read (500 lines): ~3-5k tokens
- Bash output (full): ~2-4k tokens
- Thinking block (long): ~1-3k tokens

**Track mentally**:
- Start of session: ~5-10k (system prompts)
- Every 10 responses: +10-20k
- Each file read: +3-5k
- Each command: +2-4k

**Alert at estimated**:
- 20 responses = ~40-50k (check status)
- 40 responses = ~80-100k (enable cleanup)
- 60 responses = ~120-150k (aggressive cleanup)

## Success Metrics

**Target**: Maintain <50% context throughout session

**Measurements**:
- Check token usage every 10-15 minutes
- Alert user proactively at thresholds
- Optimize without disrupting flow
- Only suggest /compact as last resort

**Good Session**:
- Never exceeded 60%
- Used incremental strategies
- Completed 2+ hours of work
- No forced interruptions

**Excellent Session**:
- Stayed under 50% entire time
- Thinking mode toggled strategically
- Selective reads and filtered outputs
- User didn't notice optimization

## Token Savings Summary

| Strategy | Timing | Per-Use Savings | Session Impact |
|----------|--------|-----------------|----------------|
| MCP Optimization | Session start | 15-25k tokens | 7-12% budget |
| Thinking Suppression | Per response | 2-3k tokens | 20-30% per response |
| Selective Reading | Per file | 8-15k tokens | 70-85% per file |
| Output Filtering | Per command | 3-8k tokens | 60-90% per command |
| Output Summarization | Per task | 5-10k tokens | 10-15% overall |
| Memory Pruning | Mid-session | 8-15k tokens | 4-7% budget |
| Codebase Survey | Multi-file reviews | 30-80k tokens | 40-60% per review |
| Strategic Deep-Dive | Per decision | 5-30k tokens | 50-80% avoided |
| Output Efficiency | Documentation | 10-30k tokens | 50-85% per doc |
| Cross-File Analysis | Architecture | 10-50k tokens | 90%+ avoided |
| **Combined Effect** | **Full session** | **~50-100k tokens** | **2-3x session capacity** |

**Example Math**:
- Without optimization: 180k tokens after 90 minutes → Emergency compaction
- With optimization: 110k tokens after 90 minutes → Continue working
- **Result**: 70k tokens saved = 35% more productive time per session

## Example Workflow

### Beginning of Session (10k tokens)
\`\`\`
✅ Context healthy at 5% (10k/200k)
Proceeding with normal operation
\`\`\`

### After 15 Minutes (45k tokens)
\`\`\`
✅ Context at 22% (45k/200k) - All good
Continuing with full thinking enabled
\`\`\`

### After 30 Minutes (85k tokens)
\`\`\`
🟡 Context at 42% (85k/200k)

Optimization enabled:
- Thinking mode: disabled for routine tasks
- File reading: selective with grep
- Command output: filtered to essentials

Continuing work...
\`\`\`

### After 45 Minutes (110k tokens)
\`\`\`
🟠 Context at 55% (110k/200k)

Active cleanup:
- Thinking: disabled except complex tasks
- Memory: pruned old sessions
- Outputs: summaries only

Recommend completing current task (RAG integration)
then starting fresh session. ETA: 10 minutes.
\`\`\`

### Task Complete (120k tokens)
\`\`\`
🟠 Context at 60% (120k/200k)

Task complete! Recommend:
1. Commit all work ✅
2. Update memory ✅
3. Start fresh session for next task

Type /end to close this session cleanly.
\`\`\`

## Anti-Patterns to Avoid

❌ **Don't**:
- Read entire files when you need 10 lines
- Show full bash output when summary works
- Keep thinking enabled for simple tasks
- Quote large sections in responses
- Re-read files you just wrote

✅ **Do**:
- Use grep/search to find, then read selectively
- Filter outputs with head/tail/grep
- Toggle thinking mode based on task complexity
- Reference files by path:line instead of quoting
- Trust tool success without verification

## Integration with Other Skills

**Works with**:
- \`verification-before-completion\`: Verify efficiently (selective reads)
- \`test-driven-development\`: Run specific tests, not full suite
- \`systematic-debugging\`: Use targeted investigation, not broad searches
- \`brainstorming\`: Disable thinking for idea capture
- \`writing-plans\`: Save detailed plans to files, not responses

**Complements**:
- USS /end command: Clean session wrap-up
- Memory rotation: Auto-archive when >500 lines
- Session logs: Details in logs, summaries in responses

---

**Remember**: The best context management is invisible to the user. Optimize continuously, alert proactively, and only disrupt when absolutely necessary.
