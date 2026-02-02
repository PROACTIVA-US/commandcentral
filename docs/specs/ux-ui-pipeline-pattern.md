---
title: UX/UI Pipeline Pattern
status: active
updated: 2026-01-28 19:51
---

# UX/UI Pipeline Pattern

> **The standard process for building any UI component in CC4**
> 
> This pattern ensures we build with INTENT, not just RULES.

---

## The Problem

Without a structured approach:
- Developers jump straight to code
- Validation checks rules but misses intent
- Research happens in conversations and gets lost
- Same mistakes repeat across components

## The Solution

**Spec → Research → Info Flow → Build → Validate → Learn**

This is The Loop applied to UI development.

---

## Phase 1: SPEC (Query KB First)

Before writing any code, query KnowledgeBeast for existing knowledge:

```bash
# What does this component need to do?
curl -X POST http://localhost:8001/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "ComponentName specification design intent", "top_k": 10}'
```

**Output:** Component spec document containing:
- Purpose (what problem it solves)
- User interactions (how users engage)
- Data requirements (what it needs)
- Rendering (what it displays)
- Constraints (what it must NOT do)

**Store in KB:**
```bash
curl -X POST http://localhost:8001/api/v1/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "...",
    "title": "ComponentName Spec",
    "source_type": "spec"
  }'
```

---

## Phase 2: RESEARCH (External Patterns)

Research how similar problems are solved elsewhere:

### What to Research
- **Competitor patterns**: How does Zoom/Figma/Notion do this?
- **Design systems**: What do Material/Ant/Chakra recommend?
- **Interaction paradigms**: What's the standard UX for this?
- **Accessibility**: What are WCAG requirements?

### How to Research
1. Web search for patterns
2. Extract key insights
3. Store in KnowledgeBeast

```bash
curl -X POST http://localhost:8001/api/v1/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Research findings for ComponentName...",
    "title": "ComponentName Research - External Patterns",
    "source_type": "research",
    "metadata": {"sources": ["zoom.us", "figma.com"]}
  }'
```

**Key insight:** Research stored in KB is reusable. Next time someone builds a similar component, they query KB first.

---

## Phase 3: INFORMATION FLOW DIAGRAM

Before coding, map how data moves:

### Template
```
User Action           →    System Response       →    Data Source
─────────────────────────────────────────────────────────────────
[User does X]              [System does Y]            [Data from Z]
```

### Questions to Answer
1. What data does this component need?
2. Where does that data come from? (API? KB? Local state?)
3. What user actions are possible?
4. What does each action trigger?
5. What state changes result?

### Output
Create `docs/specs/COMPONENTNAME-INFORMATION-FLOW.md`

**Store in KB:**
```bash
curl -X POST http://localhost:8001/api/v1/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "...",
    "title": "ComponentName Information Flow",
    "source_type": "architecture"
  }'
```

---

## Phase 4: BUILD (With Full Context)

Now code, with spec + research + info flow as context.

### Setup
```bash
# Create worktree for isolation
git worktree add ../CC4-worktrees/component-name -b feature/component-name

# Query KB for full context before coding
curl -X POST http://localhost:8001/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "ComponentName spec research architecture", "top_k": 15}'
```

### Code Structure
```
frontend/src/components/ComponentName/
├── ComponentName.tsx       # Main component
├── ComponentName.test.tsx  # Tests
├── hooks/
│   └── useComponentName.ts # Data fetching/state
├── types.ts                # TypeScript interfaces
└── index.ts                # Exports
```

### During Development
- Reference spec for intent
- Reference research for patterns
- Reference info flow for data handling
- Don't deviate without updating spec

---

## Phase 5: VALIDATE (External, Not Self-Reported)

**"AI saying 'done' is not validation."**

### Validation via API
```bash
# Run UX validation gates
curl -X POST http://localhost:8001/api/v1/ux/validate \
  -H "Content-Type: application/json" \
  -d '{
    "component": "ComponentName",
    "code_path": "frontend/src/components/ComponentName"
  }'
```

### What Gets Checked

| Gate | Validates |
|------|-----------|
| Progressive Disclosure | Info revealed incrementally |
| Composability | Reusable, combinable |
| Feature Hierarchy | Important things prominent |
| Semantic Clarity | Labels meaningful |
| Information Architecture | Logical grouping |
| Role Visibility | Appropriate for user role |

### With KB Context
Validation queries KB for spec, so it knows INTENT:
- "This button violates feature hierarchy" (rule)
- "...because the spec says X should be primary action" (intent)

### If Violations Found
```
Loop:
  1. Read violation + intent reference
  2. Query KB for similar fixes
  3. Generate fix in worktree
  4. Re-validate
  5. Repeat until passes
```

---

## Phase 6: LEARN (Store Back in KB)

After successful build, capture learnings:

```bash
curl -X POST http://localhost:8001/api/v1/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Building ComponentName, we learned: ...",
    "title": "ComponentName - Learnings",
    "source_type": "learning",
    "metadata": {"component": "ComponentName", "date": "2026-01-29"}
  }'
```

### What to Capture
- What worked well
- What didn't work (and why)
- Patterns discovered
- Gotchas for next time
- Spec updates needed

---

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UX/UI PIPELINE WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────┘

START: "Build ComponentName"
         │
         ▼
┌─────────────────┐
│   1. SPEC       │  Query KB → Generate spec → Store in KB
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   2. RESEARCH   │  Web search → Extract patterns → Store in KB
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   3. INFO FLOW  │  Map data flow → Create diagram → Store in KB
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   4. BUILD      │  Query KB for context → Code in worktree
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   5. VALIDATE   │────▶│   VIOLATIONS?   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │ NO                    │ YES
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   6. MERGE      │     │   FIX & RETRY   │──┐
└────────┬────────┘     └─────────────────┘  │
         │                       ▲            │
         │                       └────────────┘
         ▼
┌─────────────────┐
│   7. LEARN      │  Capture learnings → Store in KB
└────────┬────────┘
         │
         ▼
       DONE
```

---

## For CC4 Self-Modification

When CC4 fixes its own UI:

1. **Spec exists in KB** (we ingested it)
2. **Research exists in KB** (stored from previous sessions)
3. **Info flow exists** (CC4-INFORMATION-FLOW.md)
4. **Validation via API** (backend runs on main, validates worktree)
5. **Learnings stored** (The Loop improves itself)

This is why ingesting everything into KB first was critical.

---

## Key Principles

1. **Query KB before coding** - Don't reinvent, reuse
2. **Store research** - It's reusable knowledge
3. **Map data flow first** - Understand before building
4. **Validate externally** - Not "I think it's done"
5. **Capture learnings** - The Loop gets smarter

---

## Quick Reference

```bash
# Phase 1: Spec
curl -X POST localhost:8001/api/v1/knowledge/search -d '{"query": "ComponentName spec"}'

# Phase 2: Store research
curl -X POST localhost:8001/api/v1/knowledge/ingest -d '{"content": "...", "source_type": "research"}'

# Phase 3: Store info flow
curl -X POST localhost:8001/api/v1/knowledge/ingest -d '{"content": "...", "source_type": "architecture"}'

# Phase 4: Query context before coding
curl -X POST localhost:8001/api/v1/knowledge/search -d '{"query": "ComponentName spec research flow"}'

# Phase 5: Validate
curl -X POST localhost:8001/api/v1/ux/validate -d '{"component": "ComponentName"}'

# Phase 6: Store learnings
curl -X POST localhost:8001/api/v1/knowledge/ingest -d '{"content": "...", "source_type": "learning"}'
```
