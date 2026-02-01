---
name: cc3-build-patterns
description: Patterns for autonomous platform builds. Use when building CC3 or similar large-scale systems where the builder enriches knowledge/memory/skills during the process.
category: autonomous-development
keywords:
  - cc3
  - autonomous-build
  - self-improvement
  - the-loop
  - dogfood
---

# CC3 Build Patterns

Patterns for building CommandCenter 3.0 (and future platforms) autonomously while enriching the knowledge, memory, and skills that the new system inherits.

## Core Philosophy

> **Build while learning. Learn while building. Every insight persists.**

This isn't just a build - it's The Loop in action:
- **DISCOVER** - Find patterns, gaps, better approaches
- **VALIDATE** - Test against spec, confirm decisions
- **IMPROVE** - Update skills, enrich memory

## Pre-Task Ritual

Before starting ANY implementation task:

```
1. Read the spec section for current task
2. Query memory: "What have I learned about [task topic]?"
3. Check relevant skills: "What skills apply to [task]?"
4. Create mental model of approach
5. THEN start coding
```

## Task Execution Pattern

```python
# Pseudo-code for executing a build task

async def execute_task(task: Task):
    # 1. Prepare
    spec_section = read_spec(task.spec_reference)
    prior_knowledge = query_memory(task.topic)
    relevant_skills = find_skills(task.keywords)
    
    # 2. Plan (The Loop: DISCOVER)
    plan = create_implementation_plan(spec_section, prior_knowledge, relevant_skills)
    
    # 3. Execute with checkpoints
    for step in plan.steps:
        try:
            result = execute_step(step)
            
            # Document discoveries
            if result.has_new_pattern:
                store_memory(result.pattern, layer=PROJECT)
            
            # Validate (The Loop: VALIDATE)
            validate_against_criteria(step.criteria)
            
        except Exception as e:
            # Run triage
            triage = analyze_failure(e, step.context)
            
            if triage.should_create_skill:
                create_skill(triage.skill_name, triage.lessons)
            
            if triage.can_retry:
                retry_with_modified_approach(step, triage.suggestion)
            else:
                escalate_to_human(step, triage.analysis)
    
    # 4. Post-task (The Loop: IMPROVE)
    update_skills_with_learnings(task)
    store_completion_summary(task)
    commit_with_comprehensive_message(task)
```

## Memory Layer Usage

| Layer | When to Use | Example |
|-------|-------------|---------|
| WORKING (1) | Current task context | "Currently implementing OFAC sync" |
| SESSION (2) | Today's build progress | "Phases 0-2 complete" |
| PROJECT (3) | CC3-specific decisions | "Chose pgvector over Pinecone because..." |
| USER (4) | Build preferences | "Prefers comprehensive commit messages" |
| SYSTEM (5) | Platform patterns | "FastAPI service pattern" |
| EPISODIC (6) | Phase completions | "Phase 2 complete. Key learnings: ..." |

### Memory Entry Template

```json
{
  "layer": "PROJECT",
  "content": "Implemented OFAC SDN sync. Key decisions: ...",
  "metadata": {
    "task": "Phase 2 - OFAC Sync",
    "timestamp": "2026-01-06T10:30:00Z",
    "outcome": "success",
    "patterns_discovered": ["XML parsing with fast-xml-parser", "checksum-based change detection"],
    "difficulties": ["Treasury.gov rate limiting"],
    "solutions_applied": ["Added exponential backoff"]
  }
}
```

## Skill Creation Triggers

Create a new skill when:

1. **Pattern repeats** - Same approach used 3+ times
2. **Non-obvious solution** - Took > 30 mins to figure out
3. **Future value** - Will definitely use this again
4. **Error prevention** - Know a gotcha others will hit

### Skill Template

```markdown
---
name: [skill-name]
description: [Brief description]
category: [category]
keywords: [list, of, keywords]
---

# [Skill Name]

## When to Use
- [Trigger condition 1]
- [Trigger condition 2]

## The Pattern
[Describe the pattern]

## Implementation
[Code example]

## Common Mistakes
- [Mistake 1]
- [Mistake 2]

## Related Skills
- [Related skill 1]
```

## Commit Message Pattern

```
[phase/task]: Brief description

Detailed explanation of what was implemented.

Key decisions:
- Decision 1: Chose X because Y
- Decision 2: Used pattern Z from skill W

Patterns discovered:
- New pattern that should become a skill

Difficulties encountered:
- Issue 1: Solved by approach A
- Issue 2: Documented in memory for future reference

Test coverage:
- [ ] Unit tests for X
- [ ] Integration test for Y

Memory updated: Yes/No
Skills created/updated: [list]

Closes #issue (if applicable)
```

## Validation Checkpoints

### Per-Task Validation
```
Before moving on:
- [ ] Code compiles/runs without errors
- [ ] Matches spec requirements
- [ ] Documentation complete
- [ ] Tests pass (or written if new)
```

### Per-Phase Validation
```
Before marking phase complete:
- [ ] All tasks in phase deliverable list done
- [ ] All validation criteria from spec pass
- [ ] Memory entries for significant learnings
- [ ] Skills created for discovered patterns
- [ ] Comprehensive git commit
```

### Per-Day Validation
```
End of day:
- [ ] Session memory updated with progress
- [ ] No uncommitted work
- [ ] Next day's starting point clear
```

## When Stuck

### The Stuck Protocol

```
1. Timer: Set 15-minute limit
2. Query: "What have I tried before for similar problems?"
3. Search: Check skills for relevant patterns
4. Alternative: Try a different approach
5. Document: Note what didn't work and why
6. Escalate: If still stuck, flag for human review

Important: ALWAYS document stuck situations
- Even unsuccessful attempts teach future selves
- Memory of "what didn't work" is valuable
```

### Stuck Entry Template

```json
{
  "layer": "PROJECT",
  "content": "Got stuck on: [problem]. Tried: [approaches]. What worked: [solution or 'escalated']. Time spent: [duration].",
  "metadata": {
    "type": "stuck_resolution",
    "problem": "[description]",
    "attempts": ["attempt1", "attempt2"],
    "resolution": "[what worked or 'escalated']",
    "learnings": ["learning1", "learning2"]
  }
}
```

## Integration Patterns

### When Building Services That Use External APIs

```python
# Pattern: Always create integration wrapper

# BAD - Direct API calls scattered
response = requests.get("https://treasury.gov/ofac/...")

# GOOD - Centralized integration
class TreasuryGovIntegration:
    """
    Wrapper for Treasury.gov OFAC data.
    
    Handles:
    - Rate limiting
    - Retries
    - Caching
    - Error mapping
    """
    
    async def download_sdn_list(self) -> bytes:
        # All complexity here
        ...
```

### When Building Domain Services

```python
# Pattern: Service + Models + Router separation

# domains/veria/protocol/
#   models.py       - Data classes
#   service.py      - Business logic
#   router.py       - API endpoints (references service)

# Never put business logic in router
# Never put HTTP concerns in service
```

### When Building Frontend Components

```typescript
// Pattern: Container/Presentational split

// ScreeningContainer.tsx - fetches data, handles state
// ScreeningForm.tsx - pure props, renders UI
// ScreeningResults.tsx - pure props, renders results

// Container imports presentational, never reverse
```

## Anti-Patterns to Avoid

### 1. Building Without Spec Reference

```
❌ "I'll figure out the requirements as I go"
✅ "Let me read the spec section first"
```

### 2. Not Checking Memory First

```
❌ Start coding immediately
✅ "What have I learned about this before?" → then code
```

### 3. Solving Without Documenting

```
❌ Fix the bug, move on
✅ Fix the bug, create memory entry, maybe create skill
```

### 4. Giant Commits

```
❌ "Implemented phases 2-4" (5000 lines)
✅ Multiple commits with specific descriptions
```

### 5. Skipping Validation

```
❌ "It works on my machine, moving on"
✅ Run validation criteria, then move on
```

## Success Indicators

You're doing it right when:

1. **Memory grows** - Each day has more knowledge than before
2. **Skills compound** - New patterns become reusable
3. **Speed increases** - Later phases faster than early phases
4. **Less debugging** - Past learnings prevent repeated mistakes
5. **Comprehensive commits** - Git history tells the story

## Final Checklist

Before considering any phase complete:

- [ ] Spec requirements met
- [ ] Validation criteria pass
- [ ] Memory entries stored
- [ ] Skills created/updated if patterns discovered
- [ ] Git commit with comprehensive message
- [ ] Ready for next phase

---

*The build is the product. The learning is the legacy.*
