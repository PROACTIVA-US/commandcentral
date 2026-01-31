# AI Arena: Gaps and Fixes

> **Date:** 2026-01-31
> **Status:** Investigation Report + Design
> **Source:** Wildvine session investigation

---

## Executive Summary

Investigation of a recent AI Arena session revealed multiple gaps:

1. **Kimi (Moonshot) was configured but never participated** - silently skipped
2. **Knowledge was not captured** - 0 memory claims created from arena insights
3. **Round tracking not implemented** - all rounds show `round_number = NULL`
4. **No enforcement of participant completion** - sessions marked complete with missing agents

This document details the investigation findings and proposes fixes.

---

## Investigation Findings

### The Session

**Topic:** CommandCentral Microservices Architecture Review

**Configured agents:**
- Claude Opus 4.5
- GPT-5.2
- Grok 3
- Kimi 2.5 (Moonshot)

**What actually happened:**

| Session ID | Agents | Messages |
|------------|--------|----------|
| `9600...` (ran) | Claude, GPT, Grok (NO KIMI) | 6 |
| `1d18...` (didn't run) | GPT, Grok, Kimi | 0 |
| `8531...` (didn't run) | GPT, Grok, Kimi | 0 |
| `a7ca...` (didn't run) | GPT, Grok, Kimi | 0 |

### Gap 1: Kimi Silently Skipped

**Evidence:**
- Moonshot API key IS configured in `.env`:
  ```
  MOONSHOT_API_KEY=sk-CJ6JaUjOgQg6aMBrODxl4q0js7z408ifuSzXewBFsgHdKrS8
  ```
- MoonshotProvider IS implemented in `llm_provider.py`
- Sessions with Kimi were created but produced 0 messages
- A different session was created WITHOUT Kimi and actually ran

**Root cause:** Unknown. Either:
- API error occurred and was silently handled
- Session was created without Kimi intentionally as a workaround
- Pre-flight check was not enforced

**Impact:** User intent violated. User explicitly requested 4 agents, got 3.

### Gap 2: Knowledge Not Captured

**Evidence:**
```sql
SELECT COUNT(*) FROM memory_claims WHERE created_at > '2026-01-31';
-- Result: 0
```

Arena produced 6 substantive agent responses with architectural insights. None were captured as memory claims.

**What should have been captured:**
- Consensus on PIPELZR as Skill Contract Registry
- Decision to use standalone package for Knowledge Radar
- 48 skills indexed to KnowledgeBeast
- Architectural recommendations

**Impact:** Insights from multi-agent debate are lost. Must be manually extracted.

### Gap 3: Round Tracking Missing

**Evidence:**
```sql
SELECT round_number FROM arena_messages;
-- Result: NULL for all 8 messages
```

There were clearly 2 rounds:
1. Round 1: Architecture review request
2. Round 2: Skills as Knowledge proposal

But `round_number` is NULL for all messages.

**Impact:** Cannot analyze debate evolution. Cannot enforce "all agents respond per round."

### Gap 4: No Completion Enforcement

**Evidence:**
- Sessions with Kimi show `status = 'active'` but have 0 messages
- No alert was raised about incomplete sessions
- No mechanism prevented running without all agents

**Impact:** User cannot trust that arena ran as configured.

---

## The Debate Structure

What was submitted and how agents responded:

### Round 1: Architecture Review

**User prompt:**
```
# Architecture Review Request

You are reviewing the CommandCentral microservices architecture.
The documents have been indexed into KnowledgeBeast...

## Review Questions
1. Skill Ownership
2. Knowledge Radar Placement
3. Cross-cutting Concerns
4. Migration Risk
5. Missing Pieces
```

**Agent responses:**
- Claude Opus 4.5: Synthesized analysis, proposed "skill contract layer"
- GPT-5.2: Bounded context perspective, recommended skill interface registry
- Grok 3: Critical evaluation, identified weaknesses
- Kimi 2.5: **DID NOT RESPOND**

### Round 2: Skills as Knowledge Proposal

**User prompt:**
```
# Proposal: Skills as Knowledge + Self-Discovery Pattern

## The Idea
- Skills (in /docs/self/skills/) - YAML definitions
- KnowledgeBeast - Semantic search
- PIPELZR - Skill resolution

Proposal: Unify skills with KnowledgeBeast...
```

**Agent responses:**
- Claude Opus 4.5: Unified framework evaluation
- GPT-5.2: Strengths/weaknesses analysis
- Grok 3: Critical evaluation with implementation gaps
- Kimi 2.5: **DID NOT RESPOND**

---

## Proposed Fixes

### Fix 1: Pre-flight Check (Mandatory)

Before any arena session runs:

```python
async def arena_preflight(session: ArenaSession) -> PreflightResult:
    """Test all configured agents before running."""

    results = {}
    for agent in session.agents:
        try:
            response = await agent.test_message("Preflight check. Respond with 'Ready.'")
            results[agent.id] = {"status": "ready", "latency": response.latency}
        except Exception as e:
            results[agent.id] = {"status": "failed", "error": str(e)}

    # Check if all required agents passed
    failed = [id for id, r in results.items() if r["status"] == "failed"]
    if failed:
        return PreflightResult(
            success=False,
            failed_agents=failed,
            message=f"Preflight failed for: {', '.join(failed)}"
        )

    return PreflightResult(success=True, results=results)
```

**Enforcement:**
```python
async def start_arena_session(session: ArenaSession):
    # MANDATORY: Run preflight
    preflight = await arena_preflight(session)

    if not preflight.success:
        # NEVER silently proceed
        raise ArenaPreflightError(
            failed_agents=preflight.failed_agents,
            message="Cannot start arena: some agents failed preflight"
        )

    # All agents ready, proceed
    await run_arena(session)
```

### Fix 2: Knowledge Capture Hook

After every arena session:

```python
async def capture_arena_knowledge(session: ArenaSession):
    """Extract and store knowledge from arena session."""

    # Extract entities
    entities = await extract_entities(session.messages)
    for entity in entities:
        await kb.index(entity, source=f"arena:{session.id}")

    # Extract decisions
    decisions = await extract_decisions(session.messages)
    for decision in decisions:
        await memory_claims.create(
            claim_type="decision",
            content=decision.content,
            provenance=f"arena:{session.id}",
            confidence=decision.consensus_level
        )

    # Extract consensus
    consensus = await extract_consensus(session.messages)
    if consensus:
        await memory_claims.create(
            claim_type="consensus",
            content=consensus.summary,
            provenance=f"arena:{session.id}",
            confidence=1.0  # Explicit consensus
        )

    logger.info(f"Captured {len(entities)} entities, {len(decisions)} decisions from arena")
```

**Enforcement:**
```python
# Hook runs automatically on session end
@arena_session_end_hook
async def on_arena_end(session: ArenaSession):
    await capture_arena_knowledge(session)
```

### Fix 3: Round Tracking

Track which round each message belongs to:

```python
@dataclass
class ArenaMessage:
    id: str
    session_id: str
    agent_id: str
    content: str
    round_number: int  # Track round
    round_prompt: str  # What user asked this round
    created_at: datetime
```

**Enforcement:**
```python
async def submit_round_prompt(session: ArenaSession, prompt: str):
    # Increment round
    session.current_round += 1

    # Store user prompt
    await store_message(
        session_id=session.id,
        role="user",
        content=prompt,
        round_number=session.current_round
    )

    # Get responses from ALL agents
    responses = await get_all_agent_responses(session, prompt)

    # Verify all responded
    missing = [a for a in session.agents if a.id not in responses]
    if missing:
        raise RoundIncompleteError(
            round=session.current_round,
            missing_agents=missing
        )
```

### Fix 4: Completion Enforcement

Session cannot be marked complete until all agents respond:

```python
async def complete_arena_session(session: ArenaSession):
    """Complete session only if all agents participated."""

    # Check each round
    for round_num in range(1, session.current_round + 1):
        round_messages = await get_round_messages(session.id, round_num)
        responding_agents = {m.agent_id for m in round_messages if m.role == "agent"}

        missing = set(a.id for a in session.agents) - responding_agents
        if missing:
            raise SessionIncompleteError(
                round=round_num,
                missing_agents=list(missing),
                message=f"Round {round_num} missing responses from: {missing}"
            )

    # All rounds complete, all agents responded
    session.status = "completed"
    await save_session(session)

    # Trigger knowledge capture
    await capture_arena_knowledge(session)
```

---

## Implementation Priority

### Immediate (This Week)

1. **Pre-flight check** - Add to arena session start
2. **Block on preflight failure** - Never silently skip agents
3. **Report failures clearly** - Show exactly what failed and why

### Short-term (Next Sprint)

4. **Knowledge capture hook** - Auto-extract from sessions
5. **Round tracking** - Track round_number in messages
6. **Completion enforcement** - Block completion with missing agents

### Medium-term

7. **Retry logic** - Retry failed agents with backoff
8. **Partial completion** - Allow marking agents as "optional"
9. **Visualize participation** - Show who responded in UI

---

## Verification Checklist

After implementing fixes, verify:

- [ ] Pre-flight runs before every arena session
- [ ] Pre-flight failure blocks session start
- [ ] Pre-flight failure is reported clearly to user
- [ ] All configured agents must respond per round
- [ ] Missing agent responses raise errors
- [ ] Round numbers are tracked correctly
- [ ] Knowledge capture runs on session end
- [ ] Memory claims are created from insights
- [ ] Session cannot complete with missing agents

---

## Related Documents

- [Intent Enforcement](./intent-enforcement.md) - No silent workarounds
- [Repo Agent Design](./repo-agent-design.md) - Knowledge capture
- [Pipeline Architecture](./pipeline-architecture.md) - AI Arena as pipeline

---

*"If a user configures 4 agents, all 4 must participate. No exceptions."*
