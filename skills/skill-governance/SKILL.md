---
status: active
name: skill-governance
description: Meta-skill that ensures relevant skills are checked before work begins
trigger: session_start
priority: P0
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
# Skill Governance

This meta-skill ensures that relevant skills are discovered and consulted before work begins. It is the foundation of CommandCenter's institutional knowledge system.

## Core Principle

> **Skills are not optional documentation. They are institutional knowledge that prevents repeated mistakes.**

The pipeline hardening incident (2026-01-10) demonstrated what happens when skills exist but aren't consulted: 300 lines of plan documented problems already solved in `dagger-execution` skill.

## How It Works

### 1. Task Reception

When you receive a task, BEFORE any action:

1. Parse task for keywords
2. Check `skills/MANIFEST.yaml` for matches
3. Identify required skills by priority:
   - **P0 (Blocking)**: MUST read before proceeding
   - **P1 (Required)**: MUST acknowledge before proceeding
   - **P2 (Advisory)**: Recommended, can skip with reason

### 2. Skill Matching Algorithm

```
Input: Task description + File paths being modified
Output: List of required skills

1. Extract keywords from task (tokenize, stem, lowercase)
2. For each skill in MANIFEST:
   a. Score = keyword_matches * 10 + file_pattern_matches * 20
   b. If score > threshold: add to matches
3. Sort by (priority DESC, score DESC)
4. Return top matches by priority level
```

### 3. Enforcement Protocol

**For P0 (Blocking) skills:**
```
STOP. Before proceeding, you MUST:

1. Invoke skill via Skill tool: /skill-name
   OR
2. Read skill file directly: Read skills/<name>/SKILL.md

Required skill: [skill-name]
Reason: [keyword/file match explanation]

Type "I have read [skill-name]" to proceed.
```

**For P1 (Required) skills:**
```
Recommended reading before proceeding:
- [skill-name]: [description]

These skills contain relevant context. Acknowledge with
"Acknowledged [skill-name]" or explain why skipping.
```

**For P2 (Advisory) skills:**
```
You may also find helpful:
- [skill-name]: [description]
```

### 4. Usage Tracking

Log all skill invocations to session state:

```yaml
skill_usage:
  session_id: "2026-01-10T15:30:00"
  skills_invoked:
    - name: commandcenter-operations
      timestamp: "2026-01-10T15:30:05"
      method: "Skill tool"
      task: "Fix pipeline"
    - name: dagger-execution
      timestamp: "2026-01-10T15:31:00"
      method: "Direct read"
      task: "Fix pipeline"
  skills_skipped:
    - name: damage-control
      reason: "Not running autonomous agents"
```

## Integration Points

### Claude Code Session Start

Add to `.claude/hooks/session_start.sh`:
```bash
#!/bin/bash
# Load skill governance at session start
echo "Loading skill governance..."
cat skills/MANIFEST.yaml | python3 -c "
import yaml, sys
manifest = yaml.safe_load(sys.stdin)
p0 = [s['name'] for s in manifest['skills'] if s['priority'] == 'P0']
print(f'P0 Skills (always check): {p0}')
"
```

### CommandCenter API

The SkillGovernanceService provides:

- `POST /api/v1/skills/match` - Match task to skills
- `GET /api/v1/skills/manifest` - Get full manifest
- `POST /api/v1/skills/track` - Record skill usage
- `GET /api/v1/skills/compliance/{session_id}` - Check compliance

### Pre-Commit Hook

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Check skill compliance before commit

CHANGED_FILES=$(git diff --cached --name-only)
SKILLS_USED=$(cat .skill-usage.yaml 2>/dev/null | grep "name:" | wc -l)

# Check if any P0 file patterns match
if echo "$CHANGED_FILES" | grep -q "backend/app/services/agent_service.py"; then
  if ! grep -q "dagger-execution" .skill-usage.yaml 2>/dev/null; then
    echo "ERROR: Modified agent_service.py without consulting dagger-execution skill"
    echo "Run: claude --skill dagger-execution"
    exit 1
  fi
fi

echo "Skill compliance: OK ($SKILLS_USED skills consulted)"
```

## Quick Reference

### Check What Skills Apply

```bash
# Via API (when CC2 running)
curl -X POST http://localhost:8001/api/v1/skills/match \
  -H "Content-Type: application/json" \
  -d '{"task": "fix the pipeline", "files": ["agent_service.py"]}'

# Via CLI
python3 -c "
import yaml
manifest = yaml.safe_load(open('skills/MANIFEST.yaml'))
task = 'fix the pipeline'
for skill in manifest['skills']:
    if any(kw in task.lower() for kw in skill['keywords']):
        print(f\"{skill['priority']}: {skill['name']} - {skill['description']}\")
"
```

### Manual Skill Invocation

```bash
# Via Skill tool (in Claude Code)
/commandcenter-operations
/dagger-execution

# Via direct read
cat skills/commandcenter-operations/SKILL.md
cat skills/dagger-execution/SKILL.md
```

## Anti-Patterns

### DON'T: Skip skills because "it's quick"

Even quick fixes benefit from skill context. The "quick" pipeline fix became a 300-line hardening plan.

### DON'T: Assume you remember the skill

Skills are updated. Always re-read for current version.

### DON'T: Read skill but ignore guidance

If skill says "always use dagger mode" and you use local mode, that's a skill violation.

## Success Metrics

- **Skill invocation rate**: % of tasks where relevant skills were consulted
- **Skill compliance rate**: % of commits that followed skill guidance
- **Avoided rework**: Estimated hours saved by not rediscovering known issues

---

## Skill Archival Governance (CRITICAL)

> **The 2026-01-12 Consolidation Incident:** Skills were consolidated from 35 → 3, archiving 8,955 lines of operational knowledge without extracting key principles. This section prevents that from happening again.

### The Cardinal Rule

> **Never archive a skill without preserving its key principles in an active skill.**

### Before Archiving Any Skill

**Required Steps:**

1. **Extract Key Principles** (50-100 words)
   - What is the essence of this skill?
   - What behavior would be lost if this skill disappeared?

2. **Merge Into Active Skill**
   - Add extracted principles to the appropriate active skill
   - Reference the archived skill for detailed procedures

3. **Document the Archive Decision**
   - Why is this skill being archived?
   - What active skill now contains its principles?
   - What is lost (detailed procedures only, not principles)?

4. **Human Approval Required**
   - Major consolidations (>5 skills) require explicit human approval
   - Never batch-archive skills without review

### Skill Categories (Never Archive)

These skill types are **critical infrastructure** - never archive without replacement:

| Category | Examples | Reason |
|----------|----------|--------|
| **Meta/Governance** | skill-governance | Ensures other skills are used |
| **Safety** | damage-control | Prevents destructive commands |
| **Operational** | context-management, autonomy | Core workflow patterns |
| **Quality** | repository-hygiene, documentation-protocol | Code/doc standards |

### Archive vs Active Decision Tree

```
Is this skill about HOW to do something specific?
├── YES → Can be archived (detailed procedure)
│         BUT: Extract key principles first
└── NO → Is it about WHAT to always do/avoid?
         ├── YES → Keep active (principle/rule)
         └── NO → Review case-by-case
```

### Example: Correct Consolidation

**Before:** `documentation-protocol` (153 lines) being archived

**Wrong Way:**
```bash
mv skills/documentation-protocol skills/archive/
# Knowledge lost!
```

**Correct Way:**
```markdown
# In skills/patterns/SKILL.md, add:

## Documentation Patterns (from documentation-protocol)

### Key Principles
- Update existing documents, never create new
- Single source of truth per topic
- Required frontmatter: title, type, status, created

### Detailed Procedures
See: skills/archive/documentation-protocol/SKILL.md
```

### Recovery Protocol

If skills were archived without proper extraction:

1. Audit archived skills for lost principles
2. Restore critical skills to active status
3. Extract principles from remaining archives
4. Update governance to prevent recurrence

**The 2026-01-12 Recovery:**
- Restored: skill-governance, damage-control, context-management, repository-hygiene, documentation-protocol, autonomy
- Total: ~2,971 lines of critical knowledge restored

---

*Skills are institutional memory. Archiving without extraction is organizational amnesia.*
