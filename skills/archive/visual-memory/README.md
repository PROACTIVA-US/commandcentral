# Visual Memory Skill

**Category**: architecture  
**When to use**: Long-running projects, multi-session context, agent memory persistence

## The Problem

LLMs have limited context windows. As sessions accumulate:
- JSON context grows linearly
- At 100+ sessions, context overflows
- Important history is lost

## The Solution: Tiered Visual Memory

Store context in tiers, with older content compressed to images:

| Tier | Storage | Tokens | Purpose |
|------|---------|--------|---------|
| **HOT** | JSON | ~500 | Current session |
| **WARM** | JSON | ~2,500 | Last 5 sessions |
| **COLD** | Images | ~1,500/img | Historical summaries |
| **ARCHIVE** | Images | Variable | Cross-project patterns |

### Key Insight

**Images stay as images.** They're sent to Claude's vision API, NOT extracted back to text. This is where the massive token savings come from.

## Token Economics

```
Sessions: 500
JSON per session: 500 tokens

WITHOUT tiered memory:
  500 × 500 = 250,000 tokens (impossible)

WITH tiered memory:
  HOT:     500 tokens (1 session)
  WARM:  2,500 tokens (5 sessions)
  COLD:  4,500 tokens (3 images)
  ARCHIVE: 1,500 tokens (1 pattern)
  TOTAL: 9,000 tokens

SAVINGS: 96%
```

## When to Use

### Use Tiered Visual Memory When:
- Project spans multiple sessions
- Need to preserve decisions/discoveries across time
- Working on long-term goals
- Cross-project pattern recognition needed

### Data to Store:
- Key decisions made
- Discoveries and insights
- Progress markers
- Blockers encountered
- Files changed

## Implementation

### Loading Context

```python
from app.services.visual_memory.tiered import get_tiered_memory_service

memory = get_tiered_memory_service()
context = memory.load_context(project_id)

# context.hot -> current session JSON
# context.warm -> list of recent session JSONs
# context.cold_images -> list of PNG bytes
# context.archive_images -> list of PNG bytes
```

### Saving Sessions

```python
from app.services.visual_memory.tiered import SessionState

state = SessionState(
    session_id="abc123",
    project_id="my-project",
    timestamp=datetime.utcnow(),
    phase="improve",  # discover/validate/improve
    status="complete",
    data={
        "task": "Implement user auth",
        "key_decisions": ["Use JWT", "Chose bcrypt"],
        "discoveries": ["Rate limiting needed"],
        "files_changed": ["auth.py", "routes.py"],
        "duration_seconds": 245.3,
    }
)

memory.save_session(project_id, state)
```

### Auto-Compression

When WARM tier exceeds threshold (default: 5 sessions):
1. Oldest sessions are compressed to a summary image
2. Image stored in COLD tier
3. Original JSON archived

```python
# Happens automatically, but can be forced:
memory.compress_to_cold(project_id, old_sessions)
```

## Prompt Integration

```python
def build_prompt(task: str, context: MemoryContext, phase: str) -> str:
    parts = []
    
    # WARM tier: Recent sessions as text
    if context.warm:
        parts.append("## Recent Project History")
        for session in context.warm[-3:]:
            parts.append(f"### Session {session['session_id']}")
            if session.get('key_decisions'):
                parts.append(f"Decisions: {session['key_decisions']}")
            if session.get('discoveries'):
                parts.append(f"Discoveries: {session['discoveries']}")
    
    # COLD tier: Note that history exists
    if context.cold_images:
        parts.append(f"*{len(context.cold_images)} visual summaries available*")
    
    # Phase guidance
    parts.append(get_phase_guidance(phase))
    
    # Task
    parts.append(f"# Task\n{task}")
    
    return "\n\n".join(parts)
```

## Phase Awareness

The memory system integrates with TheLoop phases:

| Phase | Focus | Memory Usage |
|-------|-------|--------------|
| **DISCOVER** | Exploration | Load broad context, save discoveries |
| **VALIDATE** | Testing | Load specific claims, save evidence |
| **IMPROVE** | Implementation | Load decisions, save changes |

```python
PHASE_GUIDANCE = {
    "discover": "Focus on exploration. Capture ideas even if incomplete.",
    "validate": "Be rigorous. Aim for 80% confidence.",
    "improve": "Bias toward action. Ship working code.",
}
```

## Storage Structure

```
backend/memory/
├── json/
│   └── {project_id}/
│       ├── session_001.json    # WARM
│       ├── session_002.json
│       └── archived/           # Compressed originals
├── visual/
│   └── {project_id}/
│       └── summary_000.png     # COLD
└── archive/
    └── pattern_001.png         # ARCHIVE
```

## Integration with RLM

Tiered visual memory is **Layer 0** of the RLM pattern:
- Provides the corpus for decomposition
- Enables unlimited context scaling
- Makes complex reasoning viable

```python
# RLM uses memory as corpus
corpus = memory.load_as_chunks(project_id)
result = await rlm_executor.execute(task, corpus)
```

## References

- Implementation: `backend/app/services/visual_memory/`
- Tiered service: `backend/app/services/visual_memory/tiered.py`
- Agent integration: `backend/app/services/agent_service.py`
- Architecture: `docs/architecture/RLM-NATIVE-COMMANDCENTER.md`

---

*External memory enables unlimited context. Images are the compression layer.*
