---
status: active
name: patterns
description: Agent orchestration patterns and code patterns for CommandCenter
priority: P1
updated: 2026-01-13 08:35
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
  - type: api_call
    description: May call external APIs
  - type: database_write
    description: May modify database
  auth_scopes:
  - scope: file:write
    required: true
  timeouts:
    default_ms: 30000
    max_ms: 180000
---
# CommandCenter Patterns

Proven patterns for agent orchestration and CC3 development.

## Essence (50 words)

Start simple: single agent with tools. Add complexity only when measurably needed. Features in prompts, not code. Agent decides HOW. Six orchestration patterns: sequential, parallel, orchestrator-workers, evaluator-optimizer, handoff, magentic. **Docs: Update existing, never create new.** MASTER_PLAN.md is THE plan.

---

## Agent Orchestration Patterns (P0)

Based on research from Anthropic, Microsoft Azure, and OpenAI.

### Core Principle

> **Start with the simplest solution. Only add complexity when it demonstrably improves outcomes.**

A single agent with well-defined tools can handle surprisingly complex tasks. Multi-agent systems add coordination overhead.

### Pattern 1: Augmented LLM (Foundation)

The basic building block - an LLM with tools, retrieval, and memory.

```
┌─────────────────────────────────────┐
│           Augmented LLM             │
├─────────────────────────────────────┤
│  Model  │  Tools  │  Memory/RAG     │
└─────────────────────────────────────┘
```

**When to use:** Start here. Most tasks can be solved with one well-equipped agent.

**CC3 Implementation:** `agent_service.py` - Single Claude agent with tool access.

### Pattern 2: Sequential (Prompt Chaining)

Tasks broken into steps, each processing output of previous.

```
Input → [Agent 1] → [Agent 2] → [Agent n] → Result
```

**When to use:**
- Clear linear dependencies
- Progressive refinement (draft → review → polish)
- Each step adds specific value

**When to avoid:**
- Steps could run in parallel
- Need backtracking or iteration

**CC3 Implementation:** Local mode with `max_concurrent=1`

### Pattern 3: Parallel (Concurrent)

Multiple agents process same input simultaneously, results aggregated.

```
           ┌─→ [Agent 1] ─→ Result 1 ─┐
Input ─→───┼─→ [Agent 2] ─→ Result 2 ─┼─→ Aggregator → Final
           └─→ [Agent n] ─→ Result n ─┘
```

**When to use:**
- Independent subtasks (sectioning)
- Multiple perspectives needed (voting/ensemble)
- Time-sensitive scenarios

**When to avoid:**
- Agents need to build on each other's work
- Resource constraints (model quota)
- No clear conflict resolution strategy

**CC3 Implementation:** Dagger mode - isolated containers, parallel execution

### Pattern 4: Orchestrator-Workers

Central manager delegates to specialized workers dynamically.

```
              ┌─→ [Worker 1] ─┐
[Manager] ────┼─→ [Worker 2] ─┼─→ [Manager] → Result
              └─→ [Worker n] ─┘
```

**When to use:**
- Can't predict subtasks upfront
- Complex tasks requiring multiple file changes
- Search tasks needing multiple sources

**CC3 Implementation:** Pipeline orchestrator delegates to task executors

### Pattern 5: Evaluator-Optimizer (Maker-Checker)

One agent generates, another evaluates in a loop.

```
[Generator] ──→ Output ──→ [Evaluator] ──→ Feedback
     ↑                                        │
     └────────────────────────────────────────┘
```

**When to use:**
- Clear evaluation criteria exist
- Iterative refinement adds measurable value
- Human feedback could improve output

**CC3 Implementation:** PR review workflow - agent creates, reviewer evaluates

### Pattern 6: Handoff (Decentralized)

Agents transfer control to each other based on specialization.

```
[Triage] ─→ [Technical] ─→ [Financial] ─→ Result
                ↓
            [Human]
```

**When to use:**
- Optimal agent not known upfront
- Multiple domain expertise needed
- Clear signals for when to transfer

**When to avoid:**
- Risk of infinite handoff loops
- Simple deterministic routing suffices

### Pattern 7: Magentic (Task Ledger)

For open-ended problems - builds and refines approach dynamically.

```
[Manager] ←→ [Task Ledger]
    │
    ├─→ [Agent 1] ←→ External Systems
    ├─→ [Agent 2] ←→ External Systems
    └─→ [Agent n] ←→ External Systems
```

**When to use:**
- No predetermined solution path
- Need documented plan before execution
- Complex, open-ended problems

**When to avoid:**
- Solution path is known
- Time-sensitive (builds plan first)
- Low complexity tasks

---

## Agent Design Principles

### Three Core Principles (Anthropic)

1. **Simplicity** - Minimize agent complexity
2. **Transparency** - Show planning steps explicitly
3. **ACI (Agent-Computer Interface)** - Invest as much in tool design as HCI

### Tool Engineering (Critical)

> Spend as much time on tool design as on prompts.

**Best practices:**
- Give model tokens to "think" before acting
- Keep format close to natural text patterns
- Avoid formatting overhead (character counting, escaping)
- Write tool descriptions like docstrings for junior developers
- Test extensively - iterate on tool definitions

### Guardrails Layers

```
┌─────────────────────────────────────┐
│         Input Guardrails            │
├─────────────────────────────────────┤
│  Relevance  │  Safety  │  PII      │
├─────────────────────────────────────┤
│         Agent Execution             │
├─────────────────────────────────────┤
│  Tool Risk  │  Human   │  Output   │
│  Rating     │  Loop    │  Validation│
└─────────────────────────────────────┘
```

**Types:**
- Relevance classifier (off-topic detection)
- Safety classifier (jailbreak/injection)
- PII filter
- Tool safeguards (risk ratings: low/medium/high)
- Output validation (brand alignment)

### Human Intervention Triggers

1. **Exceeding failure thresholds** - Max retries reached
2. **High-risk actions** - Irreversible, sensitive, high-stakes

---

## Documentation Patterns

### The Cardinal Rule

> **Update existing documents. Never create new ones unless required.**

```
# BAD - Creates parallel document
Created docs/plans/PHASE4_MVP_EXECUTION.md

# GOOD - Expands existing document
Updated docs/plans/MASTER_PLAN.md with Phase 4 details
```

### Source of Truth Files

| Document | Purpose | Rule |
|----------|---------|------|
| `MASTER_PLAN.md` | All execution phases | Add phases here |
| `NEXT_STEPS.md` | Current priorities | Update status here |
| `commandcenter3.md` | Feature spec | Expand sections here |
| `e2e-test.md` | Test spec and logs | Record results here |

---

## Frontend Patterns

### Component Principles

1. **Single Responsibility** - One component, one job
2. **Prop-Driven** - Data via props, not stores
3. **Composition** - Small parts > big blobs
4. **Size Limits** - <150 lines per component

---

## Anti-Patterns to Avoid

### Agent Anti-Patterns

```python
# BAD - Developer decides model
if complexity == "simple": return "haiku"

# GOOD - Agent decides
await orchestrator.run("Configure for: {task}")
```

### Orchestration Anti-Patterns

1. **Premature multi-agent** - Using 5 agents when 1 + tools works
2. **Hidden complexity** - Frameworks that obscure prompts
3. **Tool overload** - 15+ similar tools confuse model
4. **Ignoring latency** - Multi-hop overhead ignored
5. **Shared mutable state** - Async updates without sync

### Documentation Anti-Patterns

1. Creating new plans instead of updating MASTER_PLAN
2. Files in wrong directories
3. Missing/invalid frontmatter timestamps

---

## Implementation Checklist

### Before Building Multi-Agent

- [ ] Single agent with tools tried and failed?
- [ ] Performance baseline established with best model?
- [ ] Evals set up to measure improvement?
- [ ] Clear reason for additional complexity?

### For Each Agent

- [ ] Model selection justified (capability vs cost/latency)
- [ ] Tools well-documented with examples
- [ ] Instructions explicit and unambiguous
- [ ] Guardrails in place
- [ ] Human escalation path defined

---

*Simple first. Measure before adding complexity. Trust agent intelligence.*
