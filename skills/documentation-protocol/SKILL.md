---
name: documentation-protocol
status: active
category: governance
description: Update existing docs, never create new. Single source of truth. Proper frontmatter and naming conventions.
updated: 2026-01-31 09:40
contract:
  version: '1.0'
  inputs:
    required: []
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
# Documentation Protocol Skill

Standards for project documentation structure, naming, and frontmatter.

**CRITICAL:** This skill is frequently ignored. Enforce via hooks and validation.

## When to Use

- Creating any new documentation file
- Moving or renaming documents
- Reviewing documentation for compliance
- Setting up new projects

## Key Rules (MUST FOLLOW)

1. **ONE MASTER_PLAN.md** - Never create new plans, update the master
2. **Timestamps include time** - Format: `YYYY-MM-DD HH:MM` (e.g., `2026-01-12 15:45`)
3. **Update, don't create** - Check existing docs before creating new ones
4. **Lowercase kebab-case** - No uppercase, no underscores

## Directory Structure

```
docs/
├── MANIFEST.yaml                     # Machine-readable schema (source of truth)
├── index.md                          # Docs landing page
│
├── specs/                            # WHAT to build (evergreen, rarely change)
│   └── commandcenter3.md             # THE spec - no date suffix needed
│
├── plans/                            # HOW/WHEN to build
│   └── MASTER_PLAN.md                # SINGLE source of truth - UPDATE, don't create new
│
├── architecture/                     # System design (evergreen)
│   └── {system-name}.md
│
├── decisions/                        # ADRs - why we chose X
│   └── {NNN}-{slug}.md               # e.g., 001-use-fastapi.md
│
└── reference/                        # Guides, how-tos, API docs
    └── {topic}.md
```

## File Naming Rules

| Rule | Correct | Incorrect |
|------|---------|-----------|
| Lowercase only | `memory-system.md` | `Memory-System.md` |
| Hyphens for spaces | `memory-system.md` | `memory_system.md` |
| No dates in filename | `memory-system.md` | `memory-system-01-10.md` |
| No status prefixes | `memory-system.md` | `WIP-memory-system.md` |
| No version suffixes | `memory-system.md` | `memory-system-v2.md` |

**Key principle:** Timestamps go in frontmatter `updated:` field, NOT in filenames. Format: `YYYY-MM-DD HH:MM`

## Required Frontmatter

Every markdown doc in `docs/` MUST have YAML frontmatter:

```yaml
---
title: Human-Readable Title
type: spec | plan | architecture | decision | reference
status: draft | active | completed | archived | deprecated
created: YYYY-MM-DD
updated: YYYY-MM-DD HH:MM    # MUST include time, e.g., 2026-01-12 15:45
owner: name
tags: [relevant, tags]
---
```

**CRITICAL:** The `updated:` field MUST include hours and minutes. Date-only is NOT acceptable.

### Additional Fields by Type

```yaml
# For specs
priority: high | medium | low

# For plans
spec_source: specs/feature-name.md
progress: 0-100
current_batch: N

# For decisions (ADRs)
decision_date: YYYY-MM-DD
supersedes: NNN  # if replacing older ADR
superseded_by: NNN  # if replaced by newer ADR
```

## Where to Put Things

| Creating... | Location | Action |
|-------------|----------|--------|
| Feature requirements | `docs/specs/` | UPDATE `commandcenter3.md`, don't create new |
| Implementation plan | `docs/plans/` | UPDATE `MASTER_PLAN.md`, NEVER create new |
| System design doc | `docs/architecture/` | `{system-name}.md` - no dates |
| "Why we chose X" | `docs/decisions/` | `{NNN}-{slug}.md` - no dates |
| How-to guide | `docs/reference/` | `{topic}.md` - no dates |

**REMINDER:** One master plan. Update existing docs. Timestamps in frontmatter only.

## Forbidden Patterns

DO NOT create files matching:

- `docs/**/*HANDOFF*` - Use `status: handoff` in frontmatter
- `docs/**/*WIP*` - Use `status: draft` in frontmatter
- `docs/**/*-v[0-9]*` - Use git history for versions
- `*.md` in project root (except README, AGENTS, CLAUDE, CONTRIBUTING)
- `docs/*.md` directly (except index.md) - must be in subdirectory

## ADR Format

Example filename: `001-use-fastapi.md` (NO dates in filename)

```markdown
---
title: Use X for Y
type: decision
status: accepted
created: 2026-01-12
updated: 2026-01-12 15:45    # Includes time!
owner: name
decision_date: 2026-01-12
tags: [architecture, component]
---

# ADR-001: Use X for Y

## Context
What problem are we solving?

## Decision
We will use X.

## Consequences
- Positive: ...
- Negative: ...
```

## Enforcement

Protocol enforced via:
- `AGENTS.md` - Universal AI instructions
- `CLAUDE.md` - Claude-specific extensions
- `docs/MANIFEST.yaml` - Machine-readable rules
- Hygiene agent - Scans, detects, fixes violations

## Quick Checklist

Before creating/modifying docs:

- [ ] **UPDATE existing doc instead of creating new?** (MASTER_PLAN, commandcenter3.md)
- [ ] File in correct directory?
- [ ] Lowercase with hyphens, NO dates in filename?
- [ ] Has required frontmatter with `updated: YYYY-MM-DD HH:MM`?
- [ ] Frontmatter `updated` includes time (hours:minutes)?
- [ ] Links to related docs?

---

*Documentation compounds. One source of truth per topic. Update, don't proliferate.*
