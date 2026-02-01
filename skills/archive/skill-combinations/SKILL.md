---
name: skill-combinations
description: Guide for combining skills into effective workflows for complex tasks like refactoring, audits, and feature development
---

# Skill Combinations Guide

This guide shows how to combine CommandCenter skills into powerful workflows. Individual skills are tools; combinations are solutions.

## Available Skills Matrix

| Skill | Category | Primary Use | Typical Duration |
|-------|----------|-------------|------------------|
| **autonomy** | Execution | Long-running tasks requiring persistence (TDD loops, refactoring) | 30-120 min |
| **context-management** | Optimization | Maintain context under 50% capacity throughout sessions | Always active |
| **project-health** | Assessment | Comprehensive project audit before major work | 15-30 min |
| **agent-sandboxes** | Parallelization | Run multiple isolated agents simultaneously | 20-90 min |
| **infrastructure-decisions** | Design | Choose between infrastructure approaches (Dagger vs Compose) | 10-20 min |
| **repository-hygiene** | Maintenance | Keep repository clean and organized | 5-10 min |

## Quick Decision Matrix

**"I want to..."** → **Use these skills**

| Goal | Skill Combination | Why |
|------|------------------|-----|
| Implement a large feature | brainstorming → writing-plans → **autonomy** + **context-management** | Persistence for multi-step implementation with context efficiency |
| Refactor a major component | **project-health** → writing-plans → **autonomy** + **context-management** | Understand current state, plan, execute with persistence |
| Run comprehensive audit | **project-health** + **agent-sandboxes** (parallel) | Multiple agents audit different aspects simultaneously |
| Set up infrastructure | **infrastructure-decisions** → implementation | Choose right approach before building |
| Clean up messy repository | **project-health** → **repository-hygiene** + **autonomy** | Audit what needs cleaning, then systematically execute |
| Develop feature on tight deadline | **agent-sandboxes** (parallel streams) + **autonomy** (per stream) | Parallel work streams with persistence in each |
| Implement with tests | **autonomy** (TDD loop) + **context-management** | Persistent test-fix cycles with efficient context |
| Quarterly project review | **project-health** → **repository-hygiene** → summary report | Full assessment and cleanup |

## Workflow Recipes

### Recipe 1: Large Feature Implementation

**Scenario:** Implementing a complex feature like user authentication system with multiple components (models, routes, middleware, tests).

**Skills:** brainstorming → writing-plans → autonomy + context-management

**Workflow:**

1. **Brainstorming Phase (10-15 min)**
   - Explore requirements and constraints
   - Consider different approaches
   - Identify components needed

2. **Planning Phase (10-15 min)**
   - Create detailed implementation plan
   - Break down into testable tasks
   - Define success criteria

3. **Execution Phase (60-90 min)**
   ```bash
   # Enable context optimization from start
   /start

   # Use Ralph loop for persistence
   /ralph loop "Implement user authentication system according to plan in docs/plans/auth-system.md:
   1. Create User model with password hashing
   2. Create auth routes (login, logout, register)
   3. Add JWT middleware
   4. Write tests for each component
   5. Run tests after each step and fix failures

   Follow TDD approach. Commit after each working component." \
     --max-iterations 50 \
     --completion-promise "All components implemented, all tests passing, all work committed"
   ```

**Key Benefits:**
- **autonomy**: Persists through all implementation steps without manual intervention
- **context-management**: Keeps session efficient during long execution
- Planning provides clear roadmap for autonomous execution

**Expected Outcome:**
- Complete feature with tests
- Multiple atomic commits
- 60-90 minutes of unattended work

---

### Recipe 2: Comprehensive Project Audit

**Scenario:** Need to understand current state of a project before making major architectural decisions. Want to audit code quality, documentation, test coverage, security, and dependencies simultaneously.

**Skills:** project-health + agent-sandboxes (parallel)

**Workflow:**

1. **Setup Audit Prompts (10 min)**
   ```bash
   mkdir -p prompts/audit

   # Create 4 specialized audit prompts
   # prompts/audit/01-code-quality.md
   # prompts/audit/02-security.md
   # prompts/audit/03-documentation.md
   # prompts/audit/04-dependencies.md
   ```

2. **Launch Parallel Agents (60 min unattended)**
   ```bash
   cd ~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows

   # Launch 4 agents in parallel (separate terminals or tmux)
   uv run obox https://github.com/org/repo \
     -p prompts/audit/01-code-quality.md \
     -b audit/code-quality -f 1

   uv run obox https://github.com/org/repo \
     -p prompts/audit/02-security.md \
     -b audit/security -f 1

   uv run obox https://github.com/org/repo \
     -p prompts/audit/03-documentation.md \
     -b audit/documentation -f 1

   uv run obox https://github.com/org/repo \
     -p prompts/audit/04-dependencies.md \
     -b audit/dependencies -f 1
   ```

3. **Each Agent Uses project-health Internally**
   - Audits their specific domain comprehensively
   - Generates detailed report
   - Commits findings to their branch

4. **Consolidation (15 min)**
   - Review all 4 audit reports
   - Create master summary
   - Prioritize action items

**Key Benefits:**
- **agent-sandboxes**: 4 agents work simultaneously, 4x faster than serial
- **project-health**: Each agent uses thorough assessment methodology
- Context isolation: Each agent has full 200k context window
- Parallel execution: 60 min vs 240 min serial

**Expected Outcome:**
- 4 comprehensive audit reports (code, security, docs, deps)
- Master summary with prioritized recommendations
- 60 minutes total vs 4 hours serial

---

### Recipe 3: Multi-Stream Feature Development

**Scenario:** Working on a release with 4 independent features that need to ship together. Each feature is complex enough to need persistence.

**Skills:** agent-sandboxes (parallel) + autonomy (per agent)

**Workflow:**

1. **Create Feature Plans (20 min)**
   ```bash
   mkdir -p prompts/features

   # Create detailed prompts for each feature
   # prompts/features/01-api-versioning.md
   # prompts/features/02-rate-limiting.md
   # prompts/features/03-webhooks.md
   # prompts/features/04-admin-dashboard.md
   ```

2. **Each Prompt Includes Ralph Loop**
   ```markdown
   # Feature: API Versioning

   ## Implementation

   Use Ralph loop for persistence:

   /ralph loop "Implement API versioning:
   1. Add version prefix to all routes (/v1/, /v2/)
   2. Create version middleware
   3. Add deprecation headers
   4. Write tests
   5. Update documentation

   Run tests after each step. Fix failures before proceeding." \
     --max-iterations 30 \
     --completion-promise "All steps complete, all tests passing"
   ```

3. **Launch 4 Parallel Streams (90 min unattended)**
   ```bash
   # Each agent runs autonomously with Ralph loop
   uv run obox https://github.com/org/repo -p prompts/features/01-api-versioning.md -b feature/api-versioning -m sonnet
   uv run obox https://github.com/org/repo -p prompts/features/02-rate-limiting.md -b feature/rate-limiting -m sonnet
   uv run obox https://github.com/org/repo -p prompts/features/03-webhooks.md -b feature/webhooks -m sonnet
   uv run obox https://github.com/org/repo -p prompts/features/04-admin-dashboard.md -b feature/admin-dashboard -m sonnet
   ```

4. **Integration (30 min)**
   - Review 4 completed features
   - Test integration
   - Create release PR

**Key Benefits:**
- **agent-sandboxes**: 4 features developed simultaneously
- **autonomy**: Each agent persists through complex implementation
- Isolated contexts: No interference between features
- Commit strategy: Each feature on separate branch

**Expected Outcome:**
- 4 complete features with tests
- Each on separate branch ready for PR
- 90 minutes vs 6 hours serial development

---

### Recipe 4: Legacy Codebase Modernization

**Scenario:** Large legacy codebase needs systematic refactoring: update dependencies, fix deprecations, improve test coverage, update documentation.

**Skills:** project-health → writing-plans → autonomy + context-management + repository-hygiene

**Workflow:**

1. **Health Assessment (30 min)**
   ```bash
   # Run comprehensive assessment
   /ralph loop "Execute project-health assessment:
   1. Audit code structure and patterns
   2. Check dependency versions and vulnerabilities
   3. Assess test coverage
   4. Review documentation freshness
   5. Identify technical debt
   6. Generate detailed report

   Write findings to docs/audits/modernization-assessment.md" \
     --max-iterations 15 \
     --completion-promise "Assessment report exists and is complete"
   ```

2. **Prioritization & Planning (20 min)**
   - Review assessment report
   - Prioritize work (critical security fixes first)
   - Create detailed modernization plan
   - Break into phases

3. **Phase 1: Critical Fixes (45 min)**
   ```bash
   /ralph loop "Phase 1 - Critical Security & Dependency Updates:
   1. Update dependencies with known vulnerabilities
   2. Fix breaking changes from updates
   3. Run full test suite after each update
   4. Fix any test failures
   5. Commit after each successful update

   Work through dependencies in docs/plans/modernization-phase1.md" \
     --max-iterations 30 \
     --completion-promise "All critical dependencies updated, all tests passing"
   ```

4. **Phase 2: Code Quality (60 min)**
   ```bash
   /ralph loop "Phase 2 - Refactor Deprecated Patterns:
   1. Replace deprecated API calls
   2. Modernize async patterns
   3. Update to current best practices
   4. Add missing type hints
   5. Run tests and linting after each change

   Work through items in docs/plans/modernization-phase2.md" \
     --max-iterations 40 \
     --completion-promise "All deprecated patterns replaced, tests passing, linting clean"
   ```

5. **Cleanup & Documentation (20 min)**
   - Apply repository-hygiene rules
   - Move misplaced files to proper locations
   - Update documentation to reflect changes
   - Archive stale docs

**Key Benefits:**
- **project-health**: Provides complete baseline understanding
- **autonomy**: Persists through tedious refactoring work
- **context-management**: Keeps session efficient during long execution
- **repository-hygiene**: Ensures clean final state
- Phased approach: Break overwhelming task into manageable pieces

**Expected Outcome:**
- Modernized codebase with current dependencies
- Improved code quality and test coverage
- Clean repository structure
- Updated documentation
- ~3 hours vs days of manual work

---

### Recipe 5: Infrastructure Setup with Testing Matrix

**Scenario:** Need to set up infrastructure for a new service that will support multiple database backends (for flexibility). Need to make informed decisions and implement with tests.

**Skills:** infrastructure-decisions → implementation → autonomy (for test matrix)

**Workflow:**

1. **Decision Phase (15 min)**
   - Review infrastructure-decisions skill
   - Answer decision matrix questions:
     - Need custom images? (Postgres + pgvector) → YES
     - Need testing matrix? (test against multiple backends) → YES
     - Need programmatic orchestration? → YES
     - Conclusion: Use Dagger

2. **Implementation Phase (45 min)**
   ```bash
   # Create Dagger configuration with helper to start different backends
   /ralph loop "Implement Dagger-based infrastructure:
   1. Create dagger_config.py with functions to start different backends
   2. Implement postgres_with_pgvector() - custom image
   3. Implement chromadb() - standard image
   4. Implement qdrant() - standard image
   5. Create pytest fixtures using these backends
   6. Test each backend starts correctly

   Follow Universal Dagger Pattern from docs/UNIVERSAL_DAGGER_PATTERN.md" \
     --max-iterations 25 \
     --completion-promise "All 3 backends implemented and tested"
   ```

3. **Test Matrix Phase (30 min)**
   ```bash
   # Create parameterized tests that run against all backends
   /ralph loop "Implement test matrix:
   1. Create @pytest.fixture(params=['postgres', 'chromadb', 'qdrant'])
   2. Implement tests for basic operations (insert, query, delete)
   3. Run full test suite against all backends
   4. Fix any backend-specific issues
   5. Ensure 100% pass rate across all backends

   All tests must pass for all backends." \
     --max-iterations 20 \
     --completion-promise "Test suite passes against all 3 backends with 0 failures"
   ```

**Key Benefits:**
- **infrastructure-decisions**: Guides correct tool choice (Dagger vs Compose)
- **autonomy**: Persists through implementation and testing iterations
- Decision framework prevents wasted effort on wrong approach
- Testing matrix catches compatibility issues early

**Expected Outcome:**
- Correct infrastructure approach chosen with justification
- Working Dagger configuration
- Test suite that validates all supported backends
- Confidence in backend flexibility
- 90 minutes vs potential days of trial-and-error

---

## Anti-Patterns: Skills NOT to Combine

### ❌ agent-sandboxes + context-management

**Why it fails:**
- agent-sandboxes creates isolated contexts
- context-management optimizes the LOCAL context
- Each sandbox agent manages its own context independently
- Trying to apply local context optimization to sandboxes is meaningless

**Instead:**
- Use context-management in your LOCAL session
- Let sandbox agents manage their own contexts
- Monitor sandbox logs for context issues

---

### ❌ autonomy (nested Ralph loops)

**Why it fails:**
```bash
# ❌ DON'T DO THIS
/ralph loop "Phase 1 tasks, then use /ralph loop for Phase 2..." \
  --max-iterations 50 \
  --completion-promise "Both phases done"
```

**Problems:**
- Ralph loops cannot spawn nested Ralph loops
- Creates confusion about which loop controls execution
- Completion promises become ambiguous

**Instead:**
- Run sequential Ralph loops:
```bash
# Phase 1
/ralph loop "Phase 1 tasks..." \
  --max-iterations 30 \
  --completion-promise "Phase 1 complete"

# Then Phase 2
/ralph loop "Phase 2 tasks..." \
  --max-iterations 30 \
  --completion-promise "Phase 2 complete"
```

---

### ❌ project-health + autonomy (for initial assessment)

**Why it fails:**
- project-health requires judgment and synthesis
- Initial assessment needs human review of findings
- Autonomous execution works for IMPLEMENTING fixes, not DISCOVERING what needs fixing

**Instead:**
```bash
# ✅ DO THIS: Manual assessment, autonomous cleanup
# Step 1: Manual assessment
# Review project-health skill and run assessment manually

# Step 2: Once you know what to fix, use autonomy
/ralph loop "Based on assessment in docs/audit/findings.md, clean up:
1. Archive stale docs listed in section 3
2. Delete merged branches listed in section 4
3. Update outdated docs listed in section 5" \
  --max-iterations 15 \
  --completion-promise "All cleanup tasks from findings.md completed"
```

---

### ❌ repository-hygiene + agent-sandboxes (without coordination)

**Why it fails:**
- Multiple agents creating files simultaneously
- Each agent has different idea of "proper" location
- Creates conflicts and duplicate organizational structures

**Instead:**
- Apply repository-hygiene at the END after consolidating work:
```bash
# 1. Let agents complete their work
# 2. Merge branches
# 3. THEN apply hygiene:
/ralph loop "Review repository for hygiene violations:
1. Find all misplaced files in root
2. Move to proper locations (scripts/, docs/, tests/)
3. Remove temporary files
4. Verify root is clean" \
  --max-iterations 10 \
  --completion-promise "Root directory clean, all files in proper locations"
```

---

## Skill Interdependencies

### Always Active

**context-management** should be active in EVERY session:
- Invoked automatically by `/start` command
- Runs continuously in background
- Applies to all other skills

### Prerequisites

**Before Major Work:**
```
project-health → [other skills]
```
Run assessment before starting large refactoring, feature development, or cleanup.

**Before Infrastructure Implementation:**
```
infrastructure-decisions → implementation
```
Make informed choice before building.

### Complementary Pairs

| Primary Skill | Complement With | Why |
|---------------|-----------------|-----|
| autonomy | context-management | Long tasks need context efficiency |
| agent-sandboxes | autonomy (per agent) | Each sandbox can run persistent loops |
| project-health | repository-hygiene | Assessment identifies what to clean |
| writing-plans | autonomy | Plans provide clear completion criteria |

## Troubleshooting Combined Workflows

### Ralph Loop Won't Complete

**Symptom:** Loop hits max-iterations without completing

**Diagnosis:**
1. Check completion promise is achievable
2. Review loop logs for repeated failures
3. Check if tests can actually pass

**Solution:**
```bash
# Cancel stuck loop
/cancel-ralph

# Review progress
git status
git log --oneline -5

# Adjust completion promise or split into smaller loops
/ralph loop "More specific subset of work..." \
  --max-iterations 15 \
  --completion-promise "More specific, verifiable promise"
```

---

### Sandbox Agent Failed to Push

**Symptom:** Agent completed work but branch not on GitHub

**Diagnosis:**
1. Check sandbox logs: `cat sandbox_agent_working_dir/logs/*.log | grep -i push`
2. Look for "could not read Username" error
3. Check if prompt included git auth instructions

**Solution:**
Update prompt to include authentication:
```markdown
## CRITICAL: Git Authentication

Before any git push operations:

\`\`\`bash
git remote set-url origin https://\${{GITHUB_TOKEN}}@github.com/owner/repo.git
git remote -v  # Verify
\`\`\`

**You MUST do this before attempting to push.**
```

---

### Context Exhausted During Long Workflow

**Symptom:** Session becomes slow or hits context limits

**Diagnosis:**
1. Check token usage in system reminders
2. Review if context-management is active
3. Check if thinking mode is disabled for routine tasks

**Solution:**
```bash
# If >80% context used, complete current task then:
/end  # Clean session closure

# Start fresh session with context optimization
/start

# Resume work with optimizations active
```

---

## Integration with USS (Universal Session System)

### Session Start

```bash
/start  # Automatically invokes context-management
```

What happens:
- Context optimization enabled
- MCP servers optimized (unused ones disabled)
- Thinking mode defaults to disabled
- Ready for efficient long sessions

### Session End

```bash
/end  # Clean wrap-up
```

What happens:
- Commits any uncommitted work
- Updates memory with session summary
- Archives session logs
- Prepares for next session

### Skill Usage Pattern

```bash
# 1. Start session with optimization
/start

# 2. Assess project state (if needed)
# Follow project-health skill

# 3. Execute work with appropriate combination
# e.g., autonomy + context-management for large task

# 4. Apply hygiene before committing
# Follow repository-hygiene checklist

# 5. Clean session end
/end
```

---

## Checklist: Choosing the Right Combination

Use this decision tree to select skills:

### Task Complexity
- [ ] **Simple (<30 min)**: No special skills needed
- [ ] **Medium (30-90 min)**: autonomy + context-management
- [ ] **Complex (multi-hour)**: Break into phases with autonomy per phase
- [ ] **Massive (multi-day)**: agent-sandboxes for parallel work

### Parallelization Needed?
- [ ] **No**: Use single session with autonomy if needed
- [ ] **Yes**: Use agent-sandboxes with N parallel agents

### Infrastructure Decisions?
- [ ] **Yes**: Start with infrastructure-decisions
- [ ] **No**: Skip to implementation

### Project State Unknown?
- [ ] **Yes**: Start with project-health assessment
- [ ] **No**: Proceed with planned work

### Repository Messy?
- [ ] **Yes**: Apply repository-hygiene before and after work
- [ ] **No**: Just verify before commits

---

## Cost Considerations

### Agent Sandboxes Cost

Running parallel agents incurs costs:

| Configuration | Typical Cost | Use When |
|---------------|-------------|----------|
| 1 agent, 30 turns | $0.50-1.00 | Medium single task |
| 1 agent, 60 turns | $1.00-2.00 | Complex single task |
| 4 agents, 30 turns each | $2.00-4.00 | Parallel medium tasks |
| 4 agents, 60 turns each | $4.00-8.00 | Parallel complex tasks |

**Cost-saving tips:**
- Use agent-sandboxes only when parallelization provides real value
- For sequential work, use single session with autonomy
- Monitor turn count with `--max-turns` parameter

### Ralph Loop Cost

Longer loops use more tokens but complete work autonomously:

| Iterations | Typical Cost | Use When |
|------------|-------------|----------|
| 5-10 | $0.10-0.30 | Small fixes, focused refactoring |
| 15-25 | $0.30-0.70 | Medium features, moderate refactoring |
| 30-50 | $0.70-1.50 | Large features, extensive refactoring |

**Cost-saving tips:**
- Set realistic `--max-iterations` (don't over-allocate)
- Use specific completion promises to exit early when done
- Enable context-management to reduce token usage

---

## Quick Reference Card

**Print this for easy reference:**

```
SKILL COMBINATIONS CHEAT SHEET

COMMON WORKFLOWS:
├─ Large Feature:     plans → autonomy + context-mgmt
├─ Comprehensive Audit:  project-health + agent-sandboxes (parallel)
├─ Multi-Feature Release:  agent-sandboxes + autonomy (per agent)
├─ Legacy Modernization:  project-health → autonomy + hygiene
└─ Infrastructure Setup:  infra-decisions → autonomy

ANTI-PATTERNS:
├─ ❌ agent-sandboxes + local context-mgmt
├─ ❌ Nested Ralph loops
├─ ❌ project-health + autonomy (for assessment)
└─ ❌ repository-hygiene + parallel agents (without coordination)

ALWAYS ACTIVE:
└─ context-management (via /start)

BEFORE MAJOR WORK:
└─ project-health (assessment)

BEFORE COMMITTING:
└─ repository-hygiene (verify)
```

---

## Real-World Success Stories

### Case Study 1: KnowledgeBeast RAG Service Rewrite

**Challenge:** Rewrite entire RAG service with new architecture

**Combination Used:** project-health → writing-plans → autonomy + context-management

**Outcome:**
- 90-minute autonomous execution
- Complete rewrite with tests
- All tests passing
- Documentation updated
- 3 atomic commits

**Key Success Factor:** Detailed plan provided clear roadmap for autonomous execution

---

### Case Study 2: CommandCenter Multi-Skill Audit

**Challenge:** Assess project health across multiple dimensions before major release

**Combination Used:** agent-sandboxes (4 parallel) + project-health (each agent)

**Outcome:**
- 4 comprehensive audit reports (60 min parallel vs 4 hours serial)
- Security audit found 3 vulnerabilities
- Documentation audit identified 12 stale docs
- Code quality audit found 5 anti-patterns
- Dependency audit found 8 outdated packages

**Key Success Factor:** Parallel execution with context isolation

---

### Case Study 3: Infrastructure Pivot (Compose → Dagger)

**Challenge:** Needed testing matrix but built with Docker Compose initially

**Combination Used:** infrastructure-decisions → Dagger migration with autonomy

**Outcome:**
- Decision matrix showed Dagger was right choice
- Avoided wasted effort continuing with Compose
- Migrated in 45 minutes
- Test matrix working against 3 backends
- Caught 2 backend-specific bugs early

**Key Success Factor:** infrastructure-decisions prevented sunk cost fallacy

---

## Summary

**Golden Rules:**
1. **context-management** is always active (via `/start`)
2. **project-health** before major work
3. **autonomy** for persistence
4. **agent-sandboxes** for parallelization
5. **repository-hygiene** before commits
6. **infrastructure-decisions** before infrastructure work

**Most Common Combination:**
```bash
/start  # Enable context optimization
# Assess if needed: project-health
# Plan work: writing-plans
# Execute: autonomy + context-management
# Verify: repository-hygiene
/end  # Clean closure
```

**Remember:** Skills are tools. The right combination depends on your specific task, timeline, and resources. Use this guide to make informed decisions, not as rigid rules.
