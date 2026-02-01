---
name: project-health
description: Comprehensive project assessment methodology for understanding current state, identifying stale artifacts, synthesizing vision, and planning cleanup. Use before major work phases, quarterly reviews, or when project state is unclear.
---

# Project Health Assessment

Get an accurate snapshot of where a project is NOW before making decisions.

## When to Use

- Before starting major development work
- When project state is unclear or stale
- Quarterly health reviews
- Before creating project-specific skills
- After long gaps in development

## Architecture Patterns to Recognize

Adapt assessment commands based on detected project structure:

| Pattern | Characteristics | Command Adaptations |
|---------|-----------------|---------------------|
| **Service/Repository** | Services in `app/services/`, tests in `tests/` | Check both locations for test coverage |
| **Domain-Driven** | Services grouped by domain | Audit each domain separately |
| **Microservices** | Each service has its own directory with tests | Iterate per-service |
| **Monorepo** | Multiple packages in `libs/` or `packages/` | Exclude vendored code from metrics |

**Detection:**
```bash
# Check for vendored/monorepo patterns
ls libs/ packages/ 2>/dev/null && echo "Monorepo detected"

# Check for service layer
ls backend/app/services/ src/services/ 2>/dev/null && echo "Service layer detected"

# Check for domain grouping
ls backend/app/domains/ src/domains/ 2>/dev/null && echo "Domain-driven detected"
```

## Assessment Phases

### Phase 0: Quick Triage (5 minutes)

Before deep analysis, get a quick health score to determine if full assessment is needed:

```bash
# Quick health check
echo "=== QUICK HEALTH CHECK ==="
echo "Source files: $(find . -name '*.py' -o -name '*.ts' | grep -v node_modules | grep -v venv | wc -l)"
echo "Tests: $(find . -name 'test_*.py' -o -name '*.test.ts' | wc -l)"
echo "Last commit: $(git log -1 --format='%cr')"
echo "Branches: $(git branch -a | wc -l)"
echo "Worktrees: $(git worktree list | wc -l)"
echo "Docs: $(find docs/ -name '*.md' 2>/dev/null | wc -l)"
echo "Stale docs (60d): $(find docs/ -name '*.md' -mtime +60 2>/dev/null | wc -l)"
```

**Triage Decision:**
- If all metrics look good → Skip to Phase 5 (light report)
- If any red flags → Continue with full audit

### Phase 1: Code Reality

Understand what actually exists in the codebase.

```bash
# Structure overview
find . -type f -name "*.py" | head -50
find . -type f -name "*.ts" | head -50

# Test count
find . -name "test_*.py" -o -name "*.test.ts" | wc -l

# Recent commits
git log --oneline -20

# Branch status
git branch -a
git worktree list
```

#### Service Architecture Analysis

Identify duplicates, large files, and service dependencies:

```bash
# Find potential duplicate services (optimized/enhanced/simple/async variants)
ls backend/app/services/ 2>/dev/null | grep -E "(_optimized|_enhanced|_simple|_v2|_async)" || echo "No duplicates detected"

# Find large files that may need refactoring (>500 lines)
find . -name "*.py" -not -path "*/venv/*" -exec wc -l {} + 2>/dev/null | sort -rn | head -10

# Check import patterns (service dependencies)
grep -r "from.*services" backend/app/services/ 2>/dev/null | cut -d: -f2 | sort | uniq -c | sort -rn | head -10
```

#### Test Coverage Patterns

Projects organize tests differently. Check all common patterns:

```bash
# Pattern 1: Co-located tests
find backend/app/services -name "test_*.py" 2>/dev/null | wc -l

# Pattern 2: Separate test directory
find backend/tests -path "*services*" -name "test_*.py" 2>/dev/null | wc -l

# Pattern 3: Mirror structure
find tests/unit/services -name "test_*.py" 2>/dev/null | wc -l

# Pattern 4: Tests directory at project root
find tests/ -name "test_*.py" 2>/dev/null | wc -l
```

**Document:**
- Services/modules that exist
- Test coverage (rough count)
- Active vs stale branches
- Uncommitted/unpushed work

### Phase 2: Documentation Reality

Audit documentation freshness.

```bash
# List all docs
find docs/ -name "*.md" -type f

# Find stale session docs
ls -la docs/*SESSION* docs/*session* 2>/dev/null

# Check doc ages
find docs/ -name "*.md" -mtime +30 -type f  # Modified 30+ days ago
```

**Classify docs as:**
- **Current**: Actively maintained, accurate
- **Stale**: Outdated but potentially useful content
- **Archive**: Should be moved to docs/archive/
- **Delete**: No longer relevant

### Phase 3: Vision Synthesis

Extract and reconcile the intended direction.

**Key files to review:**
- `README.md` - Project overview
- `docs/ROADMAP.md` or similar - Planned phases
- `docs/plans/` - Detailed implementation plans
- `docs/concepts/` - Feature/product concepts
- `CLAUDE.md` / `AGENTS.md` - AI context

**Questions to answer:**
1. What is this project supposed to become?
2. What phases/milestones were planned?
3. Which are complete, in-progress, abandoned?
4. Has the vision changed since plans were written?

### Phase 4: Artifact Cleanup

Identify what needs cleaning.

**Stale Worktrees:**
```bash
git worktree list
# Check each: when was last commit? Is work merged?
```

**Stale Branches:**
```bash
# Show branches with last commit date
git branch -a --sort=-committerdate | head -20

# Identify branches with last activity date
git for-each-ref --sort=-committerdate refs/remotes/ \
  --format='%(committerdate:short) %(refname:short)' | head -30

# Find branches with no activity in 60+ days
git for-each-ref --sort=committerdate refs/remotes/ \
  --format='%(committerdate:short) %(refname:short)' | \
  awk -v date=$(date -d '60 days ago' +%Y-%m-%d 2>/dev/null || date -v-60d +%Y-%m-%d) '$1 < date'
```

**Stale Documentation:**
```bash
# Session files that should be archived
ls docs/CURRENT_SESSION* docs/NEXT_SESSION* 2>/dev/null

# Dated docs older than 60 days
find docs/ -name "*2025-10*" -o -name "*2025-09*" 2>/dev/null
```

**Duplicate/Conflicting Docs:**
- Multiple files covering same topic
- Plans that contradict each other
- Outdated capability lists

### Phase 5: Health Report

Generate a summary document.

```markdown
# Project Health Report - [Date]

## Current State
- **Code**: X services, Y tests, Z% coverage estimate
- **Branches**: N active, M stale
- **Documentation**: X current, Y stale, Z to archive

## Vision Status
- **Original Goal**:
- **Current Reality**:
- **Gap Analysis**:

## Cleanup Required
- [ ] Archive N stale docs
- [ ] Delete/merge M stale branches
- [ ] Clean N stale worktrees
- [ ] Update X outdated docs

## Recommendations
1. Priority 1: ...
2. Priority 2: ...
3. Priority 3: ...
```

## Example Assessments

Real-world assessments demonstrating the methodology in action.

### Example 1: Fresh Project with Minimal Cleanup

**Project**: New React dashboard (2 weeks old)

**Phase 1 - Code Reality:**
```bash
$ find . -type f -name "*.tsx" -o -name "*.ts" | grep -v node_modules | wc -l
23

$ find . -name "*.test.tsx" | wc -l
8

$ git log --oneline -5
a3b2c1d Add user profile component
e4f5g6h Implement authentication flow
i7j8k9l Setup project structure
m0n1o2p Initial commit from create-react-app
```

**Assessment:**
- 23 TypeScript files, 8 tests (~35% coverage)
- Clean git history, all commits relevant
- Single `main` branch, no worktrees
- ✅ Healthy start

**Phase 2 - Documentation Reality:**
```bash
$ find docs/ -name "*.md"
docs/README.md
docs/SETUP.md
docs/API.md

$ find docs/ -mtime +7
(empty - all docs < 1 week old)
```

**Assessment:**
- Only 3 docs, all current and relevant
- No stale artifacts
- ✅ Documentation is lean and accurate

**Phase 3 - Vision Synthesis:**

From `README.md`:
> Goal: Real-time analytics dashboard for internal team metrics
> Phase 1: Core auth and layout (✓ Complete)
> Phase 2: Widget system (⟳ In Progress)
> Phase 3: Data integration (○ Planned)

**Assessment:**
- Vision is clear and achievable
- Current work aligns with Phase 2
- No conflicting plans
- ✅ On track

**Health Report:**

```markdown
# Health Report - 2025-12-15

## Status: HEALTHY ✅

## Current State
- **Code**: 23 files, 8 tests, ~35% coverage
- **Branches**: 1 active (main)
- **Documentation**: 3 current docs, 0 stale

## Vision Status
- **Goal**: Real-time analytics dashboard
- **Progress**: Phase 1 complete, Phase 2 in progress
- **Alignment**: Current work matches plan

## Cleanup Required
- None at this time

## Recommendations
1. Continue current trajectory
2. Add integration tests before Phase 3
3. Document widget API before expanding
```

**Cleanup Script:**
```bash
# No cleanup needed - project is healthy
echo "Project status: HEALTHY - no cleanup required"
```

---

### Example 2: Stale Project with Significant Debt

**Project**: Node.js API service (6 months since last commit)

**Phase 1 - Code Reality:**
```bash
$ find . -type f -name "*.js" | grep -v node_modules | wc -l
147

$ find . -name "*.test.js" | wc -l
12

$ git log --oneline -10
f1e2d3c (6 months ago) Quick fix for prod issue
a4b5c6d (6 months ago) WIP: refactoring auth
e7f8g9h (7 months ago) Add rate limiting
...

$ git branch -a
* main
  feature/new-auth
  feature/graphql-api
  hotfix/memory-leak
  remotes/origin/main
  remotes/origin/feature/new-auth
  remotes/origin/feature/graphql-api
  remotes/origin/hotfix/memory-leak

$ git worktree list
/home/user/api-service         a4b5c6d [main]
/tmp/api-hotfix                e7f8g9h [hotfix/memory-leak]
/home/user/api-graphql         f1e2d3c [feature/graphql-api]
```

**Assessment:**
- 147 JS files, only 12 tests (~8% coverage)
- Last commit 6 months ago - stale
- 3 local branches + 3 remote branches
- 3 worktrees (2 likely abandoned)
- ⚠️ Significant technical debt

**Phase 2 - Documentation Reality:**
```bash
$ find docs/ -name "*.md"
docs/README.md
docs/API_v1.md
docs/API_v2_DRAFT.md
docs/CURRENT_SESSION_2025-06-12.md
docs/NEXT_SESSION_2025-06-13.md
docs/DEPLOYMENT.md
docs/ROADMAP_OLD.md
docs/ROADMAP_NEW.md
docs/plans/auth-refactor.md
docs/plans/graphql-migration.md
docs/archive/

$ find docs/ -mtime +90 | wc -l
7
```

**Assessment:**
- 10 docs total, 7 are 90+ days old
- Multiple stale session files
- Conflicting roadmaps (OLD vs NEW)
- Abandoned plans for auth refactor and GraphQL
- ⚠️ Documentation chaos

**Phase 3 - Vision Synthesis:**

From `ROADMAP_OLD.md` (8 months ago):
> Phase 1: Stabilize REST API (Complete)
> Phase 2: Migrate to GraphQL (In Progress)
> Phase 3: Add real-time subscriptions

From `ROADMAP_NEW.md` (6 months ago):
> Pivot: Focus on stability over features
> Q3: Fix memory leaks and auth issues
> Q4: Improve test coverage to 80%

From recent commit messages:
> "Quick fix for prod issue" (last commit)
> "WIP: refactoring auth" (abandoned)

**Assessment:**
- Vision shifted from features to stability
- GraphQL migration abandoned mid-stream
- Auth refactor started but not completed
- Memory leak fix attempted but unclear if resolved
- ⚠️ Multiple competing priorities, unclear current direction

**Phase 4 - Artifact Cleanup:**

**Stale Worktrees:**
- `/tmp/api-hotfix` - 7 months old, unclear status
- `/home/user/api-graphql` - 6 months old, abandoned

**Stale Branches:**
- `feature/graphql-api` - 6 months old, not merged
- `hotfix/memory-leak` - 7 months old, may be merged
- `feature/new-auth` - 6 months old, WIP state

**Stale Documentation:**
- `CURRENT_SESSION_2025-06-12.md` - Should be archived
- `NEXT_SESSION_2025-06-13.md` - Should be archived
- `ROADMAP_OLD.md` - Should be archived or deleted
- `API_v2_DRAFT.md` - Unclear if still relevant
- `plans/graphql-migration.md` - Abandoned, archive

**Health Report:**

```markdown
# Health Report - 2025-12-15

## Status: CRITICAL ⚠️

## Current State
- **Code**: 147 files, 12 tests, ~8% coverage
- **Last Activity**: 6 months ago
- **Branches**: 3 local + 3 remote (all stale)
- **Worktrees**: 3 (2 abandoned)
- **Documentation**: 3 current, 7 stale, 5 to archive

## Vision Status
- **Original Goal**: GraphQL migration + real-time features
- **Revised Goal**: Stability and test coverage
- **Current Reality**: Frozen mid-refactor with unresolved issues
- **Gap**: Large - multiple abandoned initiatives

## Critical Issues
1. **Stale codebase**: No activity for 6 months
2. **Low test coverage**: 8% (target was 80%)
3. **Abandoned refactors**: Auth, GraphQL both incomplete
4. **Memory leak**: Fix attempted but status unclear
5. **Documentation chaos**: Conflicting plans, stale sessions

## Cleanup Required
- [ ] Archive 5 stale documentation files
- [ ] Delete/merge 3 stale branches
- [ ] Remove 2 abandoned worktrees
- [ ] Consolidate 2 conflicting roadmaps
- [ ] Test memory leak fix or revert
- [ ] Assess GraphQL migration - continue or rollback
- [ ] Update or remove API_v2_DRAFT.md

## Recommendations
1. **PRIORITY 1**: Verify production stability (memory leak status)
2. **PRIORITY 2**: Complete cleanup script below to clear artifacts
3. **PRIORITY 3**: Make go/no-go decision on abandoned features
4. **PRIORITY 4**: Create fresh roadmap based on current reality
5. **PRIORITY 5**: Establish test coverage baseline before new work
```

**Cleanup Script:**

```bash
#!/bin/bash
# Project Health Cleanup - 2025-12-15

echo "🧹 Starting project health cleanup..."

# 1. Archive stale documentation
mkdir -p docs/archive/2025-06
mv docs/CURRENT_SESSION_2025-06-12.md docs/archive/2025-06/
mv docs/NEXT_SESSION_2025-06-13.md docs/archive/2025-06/
mv docs/ROADMAP_OLD.md docs/archive/2025-06/
mv docs/plans/graphql-migration.md docs/archive/2025-06/

echo "✓ Archived 4 stale docs"

# 2. Check branch merge status
echo "\n📊 Checking branch status..."
git branch --merged main

# If hotfix/memory-leak is merged:
# git branch -d hotfix/memory-leak
# git push origin --delete hotfix/memory-leak

# 3. Review GraphQL branch (manual decision needed)
echo "\n🔍 GraphQL migration files:"
git show feature/graphql-api:src/ --name-only | head -20

echo "\n⚠️  MANUAL DECISION NEEDED:"
echo "   - If GraphQL migration continues: Keep branch, update roadmap"
echo "   - If GraphQL abandoned: Delete branch, archive docs"

# 4. Remove abandoned worktrees
echo "\n🗑️  Removing abandoned worktrees..."
git worktree remove /tmp/api-hotfix --force
git worktree remove /home/user/api-graphql --force

echo "✓ Removed 2 abandoned worktrees"

# 5. Consolidate roadmaps
echo "\n📋 Consolidating roadmaps..."
cat > docs/ROADMAP.md << 'EOF'
# Project Roadmap - Updated 2025-12-15

## Current Status
Production API with stability concerns. Focus shifted from features to maintenance.

## Immediate Priorities (Q1 2026)
1. Verify memory leak resolution
2. Improve test coverage from 8% to 30%
3. Complete or rollback auth refactor
4. Decision on GraphQL migration

## Future Phases (TBD)
- Determined after stability achieved
EOF

rm docs/ROADMAP_NEW.md
echo "✓ Created unified ROADMAP.md"

# 6. Generate cleanup summary
echo "\n✅ Cleanup complete!"
echo "\nNext steps:"
echo "1. Review production logs for memory leak evidence"
echo "2. Run test suite: npm test"
echo "3. Make GraphQL decision within 1 week"
echo "4. Update API_v2_DRAFT.md or archive it"
echo "5. Create new session plan in docs/SESSION_2025-12-15.md"
```

**After Cleanup:**
```markdown
## Post-Cleanup State
- **Documentation**: 4 current docs, 0 stale, 4 archived
- **Branches**: 1 active (main), 2 pending decision
- **Worktrees**: 1 (main only)
- **Next Steps**: Clear and prioritized

Status improved from CRITICAL ⚠️ to NEEDS ATTENTION 🔶
```

---

### Example 3: Mid-Development with Mixed State

**Project**: Python ML pipeline (active development)

**Phase 1 - Code Reality:**
```bash
$ find . -type f -name "*.py" | grep -v venv | wc -l
89

$ find . -name "test_*.py" | wc -l
34

$ git log --oneline -10
h8i9j0k (2 days ago) Add data validation pipeline
l1m2n3o (3 days ago) Fix preprocessing bug
p4q5r6s (5 days ago) Implement feature extraction
t7u8v9w (1 week ago) Update model architecture
x0y1z2a (1 week ago) Add experiment tracking

$ git branch -a
* main
  experiment/transformer-model
  feature/data-augmentation
  remotes/origin/main
  remotes/origin/experiment/transformer-model
```

**Assessment:**
- 89 Python files, 34 tests (~38% coverage)
- Active development (last commit 2 days ago)
- 2 active branches + main
- ✅ Healthy activity level
- ⚠️ Experiment branch needs review

**Phase 2 - Documentation Reality:**
```bash
$ find docs/ -name "*.md"
docs/README.md
docs/SETUP.md
docs/DATA_PIPELINE.md
docs/MODEL_ARCHITECTURE.md
docs/experiments/2025-11-15-baseline.md
docs/experiments/2025-11-28-transformer.md
docs/experiments/2025-12-01-augmentation.md
docs/archive/

$ find docs/ -mtime +30
docs/experiments/2025-11-15-baseline.md
```

**Assessment:**
- 7 docs total, 1 is 30+ days old
- Experiment logs being maintained
- Core docs are current
- ✅ Good documentation hygiene
- 🔶 Baseline experiment can be archived

**Phase 3 - Vision Synthesis:**

From `README.md`:
> Goal: Production ML pipeline for customer churn prediction
> Target: 85% accuracy, <100ms inference

From `experiments/2025-12-01-augmentation.md`:
> Current accuracy: 82%
> Inference time: 45ms
> Next: Try transformer architecture for 3-5% accuracy boost

From branch `experiment/transformer-model`:
> 15 commits, last commit 5 days ago
> Accuracy: 79% (lower than baseline!)
> Decision needed: Continue or abandon?

**Assessment:**
- Clear goal with measurable targets
- Close to accuracy target (82% vs 85%)
- Already meeting latency target
- Experiment branch underperforming
- ⚠️ Need decision on transformer experiment

**Health Report:**

```markdown
# Health Report - 2025-12-15

## Status: HEALTHY with MINOR ISSUES 🔶

## Current State
- **Code**: 89 files, 34 tests, ~38% coverage
- **Activity**: Active (last commit 2 days ago)
- **Branches**: 2 active experiments + main
- **Documentation**: 6 current, 1 ready to archive

## Vision Status
- **Goal**: 85% accuracy, <100ms inference for churn prediction
- **Current**: 82% accuracy, 45ms inference
- **Gap**: 3% accuracy needed (latency exceeded)

## Experiments in Progress
1. **transformer-model**: 79% accuracy (underperforming)
2. **data-augmentation**: In progress, promising

## Cleanup Required
- [ ] Archive baseline experiment (30+ days old)
- [ ] Make decision on transformer experiment
- [ ] Consolidate learnings into MODEL_ARCHITECTURE.md

## Recommendations
1. **PRIORITY 1**: Review transformer experiment - likely abandon
2. **PRIORITY 2**: Focus on data-augmentation approach
3. **PRIORITY 3**: Document experiment learnings before cleanup
4. **PRIORITY 4**: Archive completed/failed experiments
```

**Cleanup Script:**

```bash
#!/bin/bash
# ML Pipeline Health Cleanup - 2025-12-15

echo "🧹 Starting project health cleanup..."

# 1. Archive old experiment
mkdir -p docs/archive/experiments
mv docs/experiments/2025-11-15-baseline.md docs/archive/experiments/

echo "✓ Archived baseline experiment"

# 2. Evaluate transformer experiment
echo "\n🔬 Transformer Experiment Summary:"
echo "-----------------------------------"
git show experiment/transformer-model:docs/experiments/2025-11-28-transformer.md

echo "\n📊 Current Performance:"
echo "  Baseline:     82% accuracy"
echo "  Transformer:  79% accuracy"
echo "  Target:       85% accuracy"
echo ""
echo "⚠️  RECOMMENDATION: Abandon transformer experiment"
echo "   Reason: Underperforming baseline by 3%"

# 3. Document learnings before deletion
cat > docs/archive/experiments/2025-11-28-transformer-postmortem.md << 'EOF'
# Transformer Experiment Postmortem

**Date**: 2025-11-15 to 2025-12-15
**Result**: FAILED - Abandoned
**Performance**: 79% accuracy (3% below baseline)

## What We Tried
- Implemented transformer architecture for sequence modeling
- Hypothesis: Better capture of temporal patterns

## Why It Failed
- Model too complex for dataset size
- Longer training time without accuracy benefit
- Inference latency increased to 120ms (exceeded target)

## Learnings
1. Current dataset benefits more from feature engineering than complex architectures
2. Simpler models meet latency requirements better
3. Focus future work on data quality and augmentation

## Next Steps
- Continue with data-augmentation approach
- Consider ensemble of simpler models
EOF

echo "✓ Created experiment postmortem"

# 4. Clean up transformer branch
git branch -D experiment/transformer-model
git push origin --delete experiment/transformer-model

echo "✓ Deleted transformer experiment branch"

# 5. Update model architecture docs
echo "\n📝 Updating MODEL_ARCHITECTURE.md with learnings..."

# Add section to existing doc
cat >> docs/MODEL_ARCHITECTURE.md << 'EOF'

## Experiment History

### Transformer Architecture (FAILED)
- **Date**: Nov 2025
- **Result**: 79% accuracy (below baseline)
- **Lesson**: Dataset too small for complex architectures
- See: `docs/archive/experiments/2025-11-28-transformer-postmortem.md`
EOF

echo "✓ Updated architecture docs"

# 6. Summary
echo "\n✅ Cleanup complete!"
echo "\nCurrent Focus:"
echo "  ✓ Main branch: 82% accuracy"
echo "  ⟳ Data augmentation: In progress"
echo "  ✗ Transformer: Abandoned (documented)"
echo ""
echo "Next steps:"
echo "1. Complete data-augmentation experiment"
echo "2. If successful, merge to main"
echo "3. Target: 85% accuracy (3% to go)"
```

**After Cleanup:**
```markdown
## Post-Cleanup State
- **Documentation**: 6 current docs, 0 stale, 2 newly archived
- **Branches**: 1 active experiment (data-augmentation)
- **Clarity**: Failed experiment documented and removed
- **Focus**: Clear path to target metrics

Status: HEALTHY ✅ - Ready for focused development
```

---

## Sample Health Reports

Complete health report templates for different scenarios.

### Report Template: Healthy Project

```markdown
# Project Health Report - [DATE]

**Project**: [Name]
**Assessed by**: [Name/Team]
**Status**: HEALTHY ✅

## Executive Summary
Project is in good health with active development, clean documentation, and clear direction. Minor cleanup recommended but no blockers.

## Code Metrics
- **Files**: X source files
- **Tests**: Y test files (~Z% coverage)
- **Last Commit**: N days ago
- **Build Status**: Passing ✅
- **Dependencies**: Up to date

## Repository Health
- **Branches**: N active, 0 stale
- **Worktrees**: Clean (1 main only)
- **Uncommitted Changes**: None
- **Merge Conflicts**: None

## Documentation Health
- **Current Docs**: N files, all accurate
- **Stale Docs**: 0
- **Missing Docs**: [List any gaps]
- **Archive Needed**: [N files if any]

## Vision Alignment
- **Stated Goal**: [From README/Roadmap]
- **Current Work**: [What's actively being built]
- **Alignment**: ✅ Current work matches stated goals
- **Blockers**: None

## Cleanup Checklist
- [ ] Optional: Archive N old docs
- [ ] Optional: Update dependency versions
- [ ] Continue current trajectory

## Next Steps
1. Continue planned development
2. Maintain current documentation hygiene
3. Review again in [timeframe]

## Recommendations
- Project is healthy - no major changes needed
- Consider [minor improvement if any]
```

---

### Report Template: Project Needing Attention

```markdown
# Project Health Report - [DATE]

**Project**: [Name]
**Assessed by**: [Name/Team]
**Status**: NEEDS ATTENTION 🔶

## Executive Summary
Project has accumulated technical and documentation debt. Requires cleanup before major new features. Estimated cleanup time: [N hours/days].

## Code Metrics
- **Files**: X source files
- **Tests**: Y test files (~Z% coverage) ⚠️ Below target
- **Last Commit**: N days ago ⚠️ Stale
- **Build Status**: [Status]
- **Dependencies**: N outdated packages

## Repository Health
- **Branches**: N total (M stale) ⚠️
- **Worktrees**: N (M abandoned) ⚠️
- **Uncommitted Changes**: [Details]
- **Merge Conflicts**: [If any]

## Documentation Health
- **Current Docs**: N files
- **Stale Docs**: M files ⚠️
- **Conflicting Docs**: [List]
- **Archive Needed**: M files

## Vision Alignment
- **Stated Goal**: [Original plan]
- **Current Reality**: [What actually exists]
- **Alignment**: ⚠️ Gaps identified
- **Blockers**: [List key issues]

## Critical Issues
1. [Issue 1]: [Description]
2. [Issue 2]: [Description]
3. [Issue 3]: [Description]

## Cleanup Checklist
- [ ] PRIORITY 1: [Most critical cleanup]
- [ ] PRIORITY 2: [Second priority]
- [ ] PRIORITY 3: [Third priority]
- [ ] Archive N stale docs
- [ ] Delete/merge M stale branches
- [ ] Remove M abandoned worktrees
- [ ] Update/consolidate conflicting docs

## Estimated Cleanup Time
- **Documentation**: N hours
- **Repository**: N hours
- **Code Review**: N hours
- **Total**: N hours/days

## Next Steps
1. Execute cleanup script (provided below)
2. Make go/no-go decisions on stale features
3. Create fresh roadmap based on current reality
4. Resume development with clean slate

## Recommendations
1. Complete cleanup before starting new features
2. [Specific recommendation 1]
3. [Specific recommendation 2]
```

---

### Report Template: Critical State

```markdown
# Project Health Report - [DATE]

**Project**: [Name]
**Assessed by**: [Name/Team]
**Status**: CRITICAL ⚠️

## Executive Summary
Project is in critical state requiring immediate attention. Multiple abandoned initiatives, unclear direction, and significant technical debt. Recommend [pause new features / major refactor / other action].

## Code Metrics
- **Files**: X source files
- **Tests**: Y test files (~Z% coverage) ❌ Critical
- **Last Commit**: N days/months ago ❌ Frozen
- **Build Status**: ❌ Failing
- **Dependencies**: N critical vulnerabilities

## Repository Health
- **Branches**: N total (M stale) ❌
- **Worktrees**: N (M abandoned) ❌
- **Uncommitted Changes**: Extensive
- **Merge Conflicts**: Multiple

## Documentation Health
- **Current Docs**: N files
- **Stale Docs**: M files ❌ Majority stale
- **Conflicting Docs**: Multiple versions ❌
- **Archive Needed**: M files (most docs)

## Vision Alignment
- **Original Goal**: [What was planned]
- **Current Reality**: [What actually exists]
- **Alignment**: ❌ Significant divergence
- **Blockers**: Multiple critical issues

## Critical Issues
1. **[CRITICAL 1]**: [Description and impact]
2. **[CRITICAL 2]**: [Description and impact]
3. **[CRITICAL 3]**: [Description and impact]
4. **[Issue 4]**: [Description]
5. **[Issue 5]**: [Description]

## Abandoned Initiatives
- [Initiative 1]: Started [date], abandoned [reason]
- [Initiative 2]: Started [date], abandoned [reason]
- [Initiative 3]: Started [date], status unclear

## Cleanup Checklist
**Phase 1 - Critical (Do First):**
- [ ] URGENT: [Most critical issue]
- [ ] URGENT: [Second critical issue]
- [ ] Verify production stability
- [ ] Address security vulnerabilities

**Phase 2 - Cleanup (Do Second):**
- [ ] Archive N stale docs
- [ ] Delete/merge M stale branches
- [ ] Remove M abandoned worktrees
- [ ] Consolidate conflicting documentation

**Phase 3 - Rebuild (Do Third):**
- [ ] Create fresh roadmap
- [ ] Document current reality
- [ ] Make go/no-go decisions on all stalled features
- [ ] Establish new baseline

## Estimated Recovery Time
- **Critical Fixes**: N days
- **Full Cleanup**: N weeks
- **Documentation Rebuild**: N weeks
- **Total Recovery**: N weeks/months

## Decision Required
⚠️ **MAJOR DECISION NEEDED:**

**Option A**: Full cleanup and recovery
- Time: [N weeks]
- Risk: [Low/Medium/High]
- Outcome: Clean slate for continued development

**Option B**: Partial salvage
- Time: [N weeks]
- Risk: [Low/Medium/High]
- Outcome: [Description]

**Option C**: Fresh start
- Time: [N weeks]
- Risk: [Low/Medium/High]
- Outcome: New project with lessons learned

**Recommendation**: [Option X] because [reasoning]

## Next Steps
1. **IMMEDIATE**: [Critical action]
2. **THIS WEEK**: [Key decisions needed]
3. **THIS MONTH**: [Cleanup execution]
4. **ONGOING**: [Long-term recovery]

## Recommendations
1. **STOP**: All new feature development
2. **START**: Cleanup and recovery process
3. **CONTINUE**: Production support only
4. [Additional recommendations]
```

---

## Common Patterns

Recurring patterns discovered during project health assessments.

### Pattern 1: Session File Accumulation

**Symptom:**
```bash
$ ls docs/*SESSION*
docs/CURRENT_SESSION_2025-10-12.md
docs/CURRENT_SESSION_2025-11-03.md
docs/CURRENT_SESSION_2025-12-01.md
docs/NEXT_SESSION_2025-10-13.md
docs/NEXT_SESSION_2025-11-04.md
```

**Root Cause:**
- Session files created but never archived
- Each session creates new files without cleanup
- Over time, accumulates noise

**Detection:**
```bash
find docs/ -name "*SESSION*" -type f | wc -l
# If > 2, cleanup needed
```

**Resolution:**
```bash
# Archive all but current
mkdir -p docs/archive/sessions
mv docs/CURRENT_SESSION_2025-1[01]*.md docs/archive/sessions/
mv docs/NEXT_SESSION_2025-1[01]*.md docs/archive/sessions/

# Keep only most recent
ls -t docs/CURRENT_SESSION* | tail -n +2 | xargs -I {} mv {} docs/archive/sessions/
```

**Prevention:**
- At session end, archive that session's files
- Use dated archive directories: `docs/archive/sessions/2025-10/`
- Maximum 2 session files in root: current + next

---

### Pattern 2: Competing Roadmaps

**Symptom:**
```bash
$ ls docs/*ROADMAP*
docs/ROADMAP.md
docs/ROADMAP_v2.md
docs/ROADMAP_NEW.md
docs/ROADMAP_REVISED.md
docs/plans/ROADMAP_2025_Q4.md
```

**Root Cause:**
- Vision changes but old docs not archived
- New versions created alongside old
- Unclear which is authoritative

**Detection:**
```bash
find docs/ -iname "*roadmap*" -type f
# If > 1, investigate for conflicts
```

**Resolution:**
```bash
# 1. Read all roadmaps
for file in $(find docs/ -iname "*roadmap*"); do
  echo "=== $file ==="
  head -20 "$file"
done

# 2. Identify the most current
# 3. Archive the rest
mkdir -p docs/archive/old-roadmaps
mv docs/ROADMAP_v2.md docs/archive/old-roadmaps/
mv docs/ROADMAP_NEW.md docs/archive/old-roadmaps/
mv docs/ROADMAP_REVISED.md docs/archive/old-roadmaps/

# 4. Rename current to canonical name
mv docs/plans/ROADMAP_2025_Q4.md docs/ROADMAP.md
```

**Prevention:**
- Single source of truth: `docs/ROADMAP.md`
- Update in place, don't create new versions
- Use git history for old versions
- Archive old roadmaps immediately when creating new

---

### Pattern 3: Abandoned Experiment Branches

**Symptom:**
```bash
$ git branch -a
  experiment/approach-a
  experiment/approach-b
  experiment/approach-c
  feature/new-feature-attempt-1
  feature/new-feature-attempt-2
  feature/new-feature-attempt-3
```

**Root Cause:**
- Experiments created but never merged or deleted
- No decision documented on success/failure
- Accumulates "what if" branches

**Detection:**
```bash
# Find branches with no activity in 30+ days
for branch in $(git branch | grep -v main); do
  last_commit=$(git log -1 --format=%ct $branch)
  now=$(date +%s)
  days=$(( ($now - $last_commit) / 86400 ))
  if [ $days -gt 30 ]; then
    echo "$branch: $days days old"
  fi
done
```

**Resolution:**
```bash
# For each old experiment branch:

# 1. Check if merged
git branch --merged main | grep experiment/approach-a

# 2. If merged, delete
git branch -d experiment/approach-a
git push origin --delete experiment/approach-a

# 3. If not merged, document outcome
mkdir -p docs/archive/experiments
cat > docs/archive/experiments/approach-a-postmortem.md << 'EOF'
# Experiment: Approach A

**Status**: Failed / Succeeded / Abandoned
**Reason**: [Why]
**Learnings**: [What we learned]
**Branch**: experiment/approach-a (deleted YYYY-MM-DD)
EOF

# 4. Then delete
git branch -D experiment/approach-a
git push origin --delete experiment/approach-a
```

**Prevention:**
- Document experiment outcomes before deletion
- Use PR descriptions for experiment results
- Delete immediately after merge or abandonment
- Keep experiment count low (max 2-3 active)

---

### Pattern 4: Duplicate Documentation

**Symptom:**
```bash
$ ls docs/API*
docs/API.md
docs/API_DOCS.md
docs/API_v2.md
docs/api-reference.md
docs/API_GUIDE.md
```

**Root Cause:**
- New docs created without checking for existing
- API versions not clearly separated
- Unclear naming conventions

**Detection:**
```bash
# Find potential duplicates
find docs/ -iname "*api*" -type f

# Check for similar content
for file in $(find docs/ -iname "*api*"); do
  echo "=== $file ==="
  wc -l "$file"
done
```

**Resolution:**
```bash
# 1. Compare content
diff docs/API.md docs/API_DOCS.md

# 2. Consolidate into single canonical doc
# Merge unique content from each
cat docs/API.md > docs/API_REFERENCE.md
cat docs/API_GUIDE.md >> docs/API_REFERENCE.md

# 3. Archive duplicates
mkdir -p docs/archive/old-api-docs
mv docs/API.md docs/archive/old-api-docs/
mv docs/API_DOCS.md docs/archive/old-api-docs/
mv docs/API_GUIDE.md docs/archive/old-api-docs/
mv docs/api-reference.md docs/archive/old-api-docs/

# 4. Keep single source
# docs/API_REFERENCE.md is now canonical
```

**Prevention:**
- One canonical doc per topic
- Clear naming convention: `docs/[TOPIC]_REFERENCE.md`
- Version in filename if needed: `docs/API_v1.md`, `docs/API_v2.md`
- Check for existing docs before creating new

---

### Pattern 5: Forgotten Worktrees

**Symptom:**
```bash
$ git worktree list
/home/user/project         a1b2c3d [main]
/tmp/hotfix-urgent         e4f5g6h [hotfix/urgent]
/tmp/project-experiment    i7j8k9l [experiment/feature]
/home/user/project-v2      m0n1o2p [feature/v2]
```

**Root Cause:**
- Worktrees created for quick fixes or experiments
- Never cleaned up after completion
- Accumulates disk space and confusion

**Detection:**
```bash
# List all worktrees
git worktree list

# Check each for recent activity
for worktree in $(git worktree list | awk '{print $1}'); do
  if [ -d "$worktree" ]; then
    last_modified=$(stat -c %Y "$worktree" 2>/dev/null || stat -f %m "$worktree")
    now=$(date +%s)
    days=$(( ($now - $last_modified) / 86400 ))
    echo "$worktree: $days since modification"
  fi
done
```

**Resolution:**
```bash
# For each stale worktree:

# 1. Check for uncommitted changes
cd /tmp/hotfix-urgent
git status

# 2. If clean or not needed, remove
cd /home/user/project
git worktree remove /tmp/hotfix-urgent

# 3. If has changes, either commit or force remove
git worktree remove --force /tmp/hotfix-urgent

# 4. Clean up branch if needed
git branch -d hotfix/urgent
```

**Prevention:**
- Use worktrees sparingly (only for parallel work)
- Clean up immediately after merge
- Document active worktrees in session notes
- Regular audit: `git worktree list`

---

### Pattern 6: Test File Drift

**Symptom:**
```bash
$ find . -name "*.py" -not -path "*/test*" | wc -l
142

$ find . -name "test_*.py" | wc -l
8

# Only 5% of files have tests!
```

**Root Cause:**
- Tests written initially, then forgotten
- New features added without tests
- No enforcement of test coverage

**Detection:**
```bash
# List files without corresponding tests
for src_file in $(find src/ -name "*.py"); do
  basename=$(basename "$src_file" .py)
  test_file="tests/test_${basename}.py"
  if [ ! -f "$test_file" ]; then
    echo "Missing test: $src_file"
  fi
done

# Coverage report
pytest --cov=src --cov-report=term-missing
```

**Resolution:**
```bash
# Create test file stubs for critical modules
for file in src/auth.py src/payment.py src/user.py; do
  module=$(basename "$file" .py)
  cat > "tests/test_${module}.py" << EOF
"""
Tests for ${module}
TODO: Implement comprehensive tests
"""

def test_${module}_placeholder():
    # TODO: Add real tests
    pass
EOF
done

# Update roadmap
echo "- [ ] Increase test coverage from 5% to 30%" >> docs/ROADMAP.md
```

**Prevention:**
- CI check: fail if coverage drops below threshold
- Require tests for new files
- Regular coverage reports
- Make test creation part of feature definition

---

## Cleanup Scripts

Ready-to-use scripts for common cleanup scenarios.

### Script 1: Comprehensive Health Check

```bash
#!/bin/bash
# comprehensive-health-check.sh
# Run this script to generate a complete project health report

OUTPUT_DIR="docs/audits"
DATE=$(date +%Y-%m-%d)
REPORT_FILE="${OUTPUT_DIR}/${DATE}-health-report.md"

echo "🏥 Running comprehensive project health check..."

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Start report
cat > "$REPORT_FILE" << EOF
# Project Health Report - $DATE

Generated by: comprehensive-health-check.sh
Project: $(basename $(pwd))

---

EOF

# Code metrics
echo "## Code Metrics" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "- **Source files**: $(find . -name "*.py" -o -name "*.js" -o -name "*.ts" | grep -v node_modules | grep -v venv | wc -l)" >> "$REPORT_FILE"
echo "- **Test files**: $(find . -name "test_*.py" -o -name "*.test.js" -o -name "*.test.ts" | wc -l)" >> "$REPORT_FILE"
echo "- **Last commit**: $(git log -1 --format='%cr')" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Branch health
echo "## Branch Health" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "### Active Branches" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
git branch -a --sort=-committerdate | head -10 >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Worktree status
echo "## Worktree Status" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
git worktree list >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Documentation audit
echo "## Documentation Audit" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "- **Total docs**: $(find docs/ -name "*.md" 2>/dev/null | wc -l)" >> "$REPORT_FILE"
echo "- **Stale (30+ days)**: $(find docs/ -name "*.md" -mtime +30 2>/dev/null | wc -l)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Stale session files
echo "### Stale Session Files" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
ls -la docs/*SESSION* 2>/dev/null >> "$REPORT_FILE" || echo "None found" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Old dated docs
echo "### Old Dated Documentation" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
find docs/ -name "*2025-[0-9][0-9]-*" -mtime +60 2>/dev/null >> "$REPORT_FILE" || echo "None found" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Cleanup recommendations
echo "## Cleanup Recommendations" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

CLEANUP_NEEDED=0

# Check for stale branches
STALE_BRANCHES=$(git for-each-ref --sort=-committerdate refs/heads/ --format='%(refname:short) %(committerdate:relative)' | grep 'months ago\|year ago' | wc -l)
if [ "$STALE_BRANCHES" -gt 0 ]; then
  echo "- [ ] Review and clean $STALE_BRANCHES stale branches" >> "$REPORT_FILE"
  CLEANUP_NEEDED=1
fi

# Check for stale docs
STALE_DOCS=$(find docs/ -name "*.md" -mtime +60 2>/dev/null | wc -l)
if [ "$STALE_DOCS" -gt 0 ]; then
  echo "- [ ] Archive $STALE_DOCS documents older than 60 days" >> "$REPORT_FILE"
  CLEANUP_NEEDED=1
fi

# Check for session files
SESSION_FILES=$(ls docs/*SESSION* 2>/dev/null | wc -l)
if [ "$SESSION_FILES" -gt 2 ]; then
  echo "- [ ] Archive old session files (found $SESSION_FILES)" >> "$REPORT_FILE"
  CLEANUP_NEEDED=1
fi

if [ "$CLEANUP_NEEDED" -eq 0 ]; then
  echo "- No cleanup needed - project is healthy! ✅" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**Report generated**: $DATE" >> "$REPORT_FILE"

echo "✅ Health check complete!"
echo "📄 Report saved to: $REPORT_FILE"
cat "$REPORT_FILE"
```

---

### Script 2: Documentation Cleanup

```bash
#!/bin/bash
# cleanup-documentation.sh
# Archives stale documentation files

echo "📚 Starting documentation cleanup..."

# Create archive structure
mkdir -p docs/archive/sessions
mkdir -p docs/archive/old-plans
mkdir -p docs/archive/experiments

# Archive old session files
echo "🗂️  Archiving session files..."
SESSION_COUNT=0
for file in docs/*SESSION*.md docs/*session*.md; do
  if [ -f "$file" ]; then
    # Keep only the 2 most recent
    mv "$file" docs/archive/sessions/
    SESSION_COUNT=$((SESSION_COUNT + 1))
  fi
done
echo "✓ Archived $SESSION_COUNT session files"

# Archive old dated docs (60+ days)
echo "📅 Archiving old dated documents..."
OLD_DOC_COUNT=0
for file in $(find docs/ -name "*202[0-9]-[0-9][0-9]-*" -mtime +60 -type f 2>/dev/null); do
  if [ -f "$file" ]; then
    month=$(echo "$file" | grep -oE '202[0-9]-[0-9][0-9]' | head -1)
    mkdir -p "docs/archive/${month}"
    mv "$file" "docs/archive/${month}/"
    OLD_DOC_COUNT=$((OLD_DOC_COUNT + 1))
  fi
done
echo "✓ Archived $OLD_DOC_COUNT old documents"

# Find and report duplicate roadmaps
echo "🗺️  Checking for duplicate roadmaps..."
ROADMAP_COUNT=$(find docs/ -maxdepth 2 -iname "*roadmap*" -type f | wc -l)
if [ "$ROADMAP_COUNT" -gt 1 ]; then
  echo "⚠️  Found $ROADMAP_COUNT roadmap files:"
  find docs/ -maxdepth 2 -iname "*roadmap*" -type f
  echo ""
  echo "Manual review needed:"
  echo "  1. Identify the current roadmap"
  echo "  2. Archive old versions: mv docs/ROADMAP_OLD.md docs/archive/old-plans/"
else
  echo "✓ Single roadmap found (healthy)"
fi

# Summary
echo ""
echo "✅ Documentation cleanup complete!"
echo ""
echo "Summary:"
echo "  - Session files archived: $SESSION_COUNT"
echo "  - Old documents archived: $OLD_DOC_COUNT"
echo "  - Roadmaps to review: $ROADMAP_COUNT"
```

---

### Script 3: Branch Cleanup

```bash
#!/bin/bash
# cleanup-branches.sh
# Identifies and removes stale branches

echo "🌿 Starting branch cleanup..."

# Delete merged branches
echo "🔀 Cleaning merged branches..."
MERGED_COUNT=$(git branch --merged main | grep -v main | grep -v '*' | wc -l)
if [ "$MERGED_COUNT" -gt 0 ]; then
  git branch --merged main | grep -v main | grep -v '*' | xargs git branch -d
  echo "✓ Deleted $MERGED_COUNT merged branches"
else
  echo "✓ No merged branches to clean"
fi

# Identify stale branches
echo ""
echo "📊 Analyzing unmerged branches..."
echo ""
echo "Branches with no activity in 60+ days:"
echo "----------------------------------------"

STALE_BRANCHES=()
for branch in $(git branch --format='%(refname:short)' | grep -v main); do
  # Get last commit date
  last_commit=$(git log -1 --format=%ct "$branch" 2>/dev/null)
  if [ -n "$last_commit" ]; then
    now=$(date +%s)
    days=$(( ($now - $last_commit) / 86400 ))

    if [ $days -gt 60 ]; then
      last_commit_msg=$(git log -1 --format='%s' "$branch")
      echo "  $branch ($days days ago)"
      echo "    Last: $last_commit_msg"
      echo ""
      STALE_BRANCHES+=("$branch")
    fi
  fi
done

if [ ${#STALE_BRANCHES[@]} -eq 0 ]; then
  echo "✓ No stale branches found"
else
  echo ""
  echo "⚠️  Found ${#STALE_BRANCHES[@]} stale branch(es)"
  echo ""
  echo "To delete these branches, run:"
  echo ""
  for branch in "${STALE_BRANCHES[@]}"; do
    echo "  git branch -D $branch"
    echo "  git push origin --delete $branch  # If pushed to remote"
  done
  echo ""
  echo "Or review each branch first:"
  for branch in "${STALE_BRANCHES[@]}"; do
    echo "  git log $branch --oneline -5"
  done
fi

echo ""
echo "✅ Branch analysis complete!"
```

---

### Script 4: Worktree Cleanup

```bash
#!/bin/bash
# cleanup-worktrees.sh
# Identifies and removes stale worktrees

echo "🌲 Starting worktree cleanup..."

# List all worktrees
WORKTREES=$(git worktree list --porcelain | grep ^worktree | cut -d' ' -f2)
MAIN_WORKTREE=$(git rev-parse --show-toplevel)

echo "📋 Current worktrees:"
git worktree list
echo ""

STALE_COUNT=0
for worktree in $WORKTREES; do
  # Skip main worktree
  if [ "$worktree" = "$MAIN_WORKTREE" ]; then
    continue
  fi

  # Check if directory exists
  if [ ! -d "$worktree" ]; then
    echo "⚠️  Worktree missing: $worktree"
    echo "   Running: git worktree prune"
    git worktree prune
    continue
  fi

  # Check last modification
  if [ -d "$worktree" ]; then
    last_modified=$(stat -c %Y "$worktree" 2>/dev/null || stat -f %m "$worktree" 2>/dev/null)
    if [ -n "$last_modified" ]; then
      now=$(date +%s)
      days=$(( ($now - $last_modified) / 86400 ))

      if [ $days -gt 30 ]; then
        echo "🗑️  Stale worktree detected: $worktree"
        echo "   Last modified: $days days ago"

        # Check for uncommitted changes
        cd "$worktree"
        if [ -n "$(git status --porcelain)" ]; then
          echo "   ⚠️  Has uncommitted changes!"
          echo "   To remove: git worktree remove --force $worktree"
        else
          echo "   Clean worktree"
          echo "   To remove: git worktree remove $worktree"
        fi
        cd - > /dev/null

        STALE_COUNT=$((STALE_COUNT + 1))
        echo ""
      fi
    fi
  fi
done

if [ $STALE_COUNT -eq 0 ]; then
  echo "✅ No stale worktrees found"
else
  echo "⚠️  Found $STALE_COUNT stale worktree(s)"
  echo ""
  echo "Review and run suggested removal commands above"
fi

echo ""
echo "✅ Worktree cleanup analysis complete!"
```

---

### Script 5: Full Project Cleanup

```bash
#!/bin/bash
# full-project-cleanup.sh
# Comprehensive cleanup of all project artifacts

set -e

echo "🧹 Starting FULL project cleanup..."
echo "⚠️  This will modify your repository!"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Cleanup cancelled"
  exit 0
fi

# Run all cleanup scripts
echo ""
echo "=== 1/4: Documentation Cleanup ==="
bash cleanup-documentation.sh

echo ""
echo "=== 2/4: Branch Cleanup ==="
bash cleanup-branches.sh

echo ""
echo "=== 3/4: Worktree Cleanup ==="
bash cleanup-worktrees.sh

echo ""
echo "=== 4/4: Health Check ==="
bash comprehensive-health-check.sh

echo ""
echo "✅ Full cleanup complete!"
echo ""
echo "Next steps:"
echo "1. Review the health report in docs/audits/"
echo "2. Delete stale branches listed above"
echo "3. Remove stale worktrees listed above"
echo "4. Commit cleanup changes:"
echo ""
echo "   git add docs/"
echo "   git commit -m 'docs: archive stale documentation'"
echo ""
```

---

## Cleanup Protocol

### Documentation Cleanup

```bash
# Create archive if needed
mkdir -p docs/archive

# Move stale session docs
mv docs/CURRENT_SESSION*.md docs/archive/
mv docs/NEXT_SESSION*.md docs/archive/

# Move old dated docs (review first)
mv docs/*2025-10*.md docs/archive/
```

### Branch Cleanup

```bash
# Delete merged local branches
git branch --merged | grep -v main | xargs git branch -d

# List remote branches to review
git branch -r --sort=-committerdate

# Delete stale remote (careful!)
git push origin --delete branch-name
```

### Worktree Cleanup

```bash
# List worktrees
git worktree list

# Remove stale worktree
git worktree remove path/to/worktree

# Or force if dirty
git worktree remove --force path/to/worktree
```

## Integration with Self-Improving Skills

After completing a health assessment:

1. **Create/update project-specific skill** with accurate baseline
2. **Document patterns** discovered during assessment
3. **Document failures** or anti-patterns found
4. **Set up retrospective** to capture future learnings

## Automation with Ralph Loop

For comprehensive assessment:

```bash
/ralph loop "Execute project-health assessment for this project:
1. Audit code structure and tests
2. Audit documentation freshness
3. Synthesize vision from roadmap and plans
4. Identify all cleanup needed
5. Generate health report

Write results to docs/audits/YYYY-MM-DD-health-report.md" \
  --max-iterations 15 \
  --completion-promise "docs/audits/YYYY-MM-DD-health-report.md exists with all sections complete"
```

## Checklist

### Assessment
- [ ] Code structure documented
- [ ] Test coverage estimated
- [ ] Branch/worktree status checked
- [ ] Documentation audited for freshness
- [ ] Vision synthesized from plans
- [ ] Gaps identified

### Cleanup
- [ ] Stale docs archived
- [ ] Stale branches deleted/merged
- [ ] Stale worktrees removed
- [ ] Duplicate docs consolidated
- [ ] Outdated docs updated or archived

### Output
- [ ] Health report written
- [ ] Cleanup tasks listed
- [ ] Recommendations prioritized
- [ ] Project skill updated (if exists)
