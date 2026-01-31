# Repo Agent Design

> **Date:** 2026-01-31
> **Status:** Design Draft
> **Source:** Wildvine session conversation
> **Location:** CommandCentral (core infrastructure)

---

## The Problem

### Current State

1. **No persistent repo understanding** - Each agent session starts fresh, re-reads files
2. **Arena insights evaporate** - Debates happen, messages stored, but knowledge isn't captured
3. **Skills are static** - Defined in YAML, not discoverable as knowledge
4. **No proactive verification** - Agents don't challenge decisions unless explicitly asked
5. **No bidirectional communication** - Agents can't talk to each other proactively

### The Gap

```
Arena Session → Messages stored → [NOTHING] → Knowledge lost
                                      ↓
                              Should become:
                                      ↓
Arena Session → Messages stored → Repo Agent captures → KnowledgeBeast indexes
                                                      → Memory claims created
                                                      → Skills discovered
```

---

## What is the Repo Agent?

A **persistent, conversational agent** that:

1. **Knows** the repository deeply (code, architecture, decisions, patterns)
2. **Captures** knowledge automatically from conversations and arena sessions
3. **Participates** in decision-making (can challenge, verify, suggest)
4. **Speaks** bidirectionally with other agents (CLI agent, arena agents)

### Not Just Another Wrapper

| Component | What It Does | Repo Agent Difference |
|-----------|--------------|----------------------|
| KnowledgeBeast | Indexes docs → retrieves chunks | **Synthesizes understanding**, not just retrieval |
| RAG | Query → relevant chunks | **Proactive**, not just reactive |
| Claude Code | Reads files on demand | **Persistent memory**, doesn't start fresh |
| Arena | Multi-agent debate | **Captures and enforces** knowledge from debates |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           REPO AGENT                                     │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    KNOWLEDGE LAYER                               │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │ KnowledgeBeast│  │ Skill Index │  │ Decision Log │           │    │
│  │  │ (vectors)     │  │ (as knowledge)│  │ (provenance) │           │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │    │
│  │         └─────────────────┼─────────────────┘                    │    │
│  │                           ▼                                      │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │              REPO UNDERSTANDING                          │    │    │
│  │  │  - Architecture patterns                                 │    │    │
│  │  │  - Code organization                                     │    │    │
│  │  │  - Decision history + rationale                          │    │    │
│  │  │  - Known issues + solutions                              │    │    │
│  │  │  - Skill capabilities + conflicts                        │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    CONVERSATION LAYER                            │    │
│  │                                                                   │    │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │    │
│  │  │    Query     │    │   Challenge  │    │    Teach     │        │    │
│  │  │ "How does X  │    │ "That approach│    │ "New pattern │        │    │
│  │  │  work?"      │    │  conflicts   │    │  discovered" │        │    │
│  │  │              │    │  with Y"     │    │              │        │    │
│  │  └──────────────┘    └──────────────┘    └──────────────┘        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    COMMUNICATION LAYER                           │    │
│  │                                                                   │    │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │    │
│  │  │  CLI Agent   │◄──►│  Arena Agents│◄──►│   Humans     │        │    │
│  │  │ (execution)  │    │  (debate)    │    │ (oversight)  │        │    │
│  │  └──────────────┘    └──────────────┘    └──────────────┘        │    │
│  │                                                                   │    │
│  │  Protocols:                                                       │    │
│  │  - MCP (for tool access)                                         │    │
│  │  - Inner Council (for decision verification)                     │    │
│  │  - Hooks (for knowledge capture triggers)                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Capabilities

### 1. Knowledge Capture (Enforced)

Every conversation/arena session automatically feeds the Repo Agent:

```python
class KnowledgeCaptureHook:
    """Runs after every conversation/arena session."""

    async def on_conversation_end(self, messages: list[Message]):
        # Extract and store
        entities = await self.extract_entities(messages)
        decisions = await self.extract_decisions(messages)
        patterns = await self.extract_patterns(messages)
        skills_used = await self.extract_skills(messages)

        # Create memory claims with provenance
        for entity in entities:
            await self.kb.index(entity, source="conversation", provenance=messages)

        for decision in decisions:
            await self.decision_log.add(decision, rationale=messages)

        # Detect skill conflicts
        conflicts = await self.detect_skill_conflicts(skills_used)
        if conflicts:
            await self.notify_repo_agent(conflicts)

    async def on_arena_session_end(self, session: ArenaSession):
        # Enforce all configured agents responded
        missing = self.get_missing_agents(session)
        if missing:
            await self.alert(f"Arena incomplete: {missing} didn't respond")

        # Extract consensus
        consensus = await self.extract_consensus(session.messages)
        await self.kb.index(consensus, source="arena", provenance=session)

        # Update repo understanding
        await self.repo_agent.update_understanding(consensus)
```

### 2. Bidirectional Communication (Inner Council)

The Repo Agent can **proactively speak** to the CLI agent:

```python
class RepoAgent:
    """Participates in decision-making, not just answers questions."""

    async def on_decision_proposed(self, decision: Decision, agent: Agent):
        """Called when any agent proposes a decision."""

        # Check against repo understanding
        conflicts = await self.check_conflicts(decision)
        precedents = await self.find_precedents(decision)
        skill_implications = await self.analyze_skill_impact(decision)

        if conflicts or self.confidence_low(decision):
            # Proactively challenge
            await self.send_to_agent(agent, Challenge(
                decision=decision,
                concern=self.format_concern(conflicts, precedents),
                suggestion=self.suggest_alternative(decision)
            ))

        if precedents:
            # Inform, even if not challenging
            await self.send_to_agent(agent, Context(
                decision=decision,
                precedents=precedents,
                note="Similar decisions were made before"
            ))

    async def send_to_agent(self, agent: Agent, message: Message):
        """Bidirectional communication with any agent."""
        if agent.protocol == "mcp":
            await self.mcp_send(agent, message)
        elif agent.protocol == "inner_council":
            await self.council_broadcast(message)
        else:
            await self.direct_send(agent, message)
```

### 3. Inner Council Integration

The Repo Agent participates in the Inner Council - a group of specialized agents that verify decisions:

```python
class InnerCouncil:
    """Group of agents that verify decisions before execution."""

    members = [
        RepoAgent(),       # Knows the codebase
        SecurityAgent(),   # Checks security implications
        ArchitectAgent(),  # Validates architecture fit
        TestAgent(),       # Considers testability
    ]

    async def verify_decision(self, decision: Decision) -> Verdict:
        """All council members review the decision."""

        verdicts = []
        for member in self.members:
            verdict = await member.review(decision)
            verdicts.append(verdict)

        # Aggregate verdicts
        if any(v.blocks for v in verdicts):
            return Verdict(
                approved=False,
                blockers=[v for v in verdicts if v.blocks],
                suggestions=self.aggregate_suggestions(verdicts)
            )

        return Verdict(
            approved=True,
            notes=[v.note for v in verdicts if v.note]
        )
```

---

## Data Model

```python
@dataclass
class RepoUnderstanding:
    """What the Repo Agent knows about the repository."""

    # Core knowledge
    architecture: ArchitectureModel  # How code is organized
    patterns: list[Pattern]          # Design patterns in use
    decisions: list[Decision]        # Historical decisions + rationale

    # Skills as knowledge
    skills: list[SkillKnowledge]     # Skills with semantic enrichment
    skill_conflicts: list[Conflict]  # Known conflicts between skills
    skill_combos: list[Combination]  # Skills that work well together

    # From arena/conversations
    consensus_items: list[Consensus]  # Agreed-upon conclusions
    open_questions: list[Question]    # Unresolved debates

    # Provenance
    sources: list[Source]            # Where knowledge came from

@dataclass
class SkillKnowledge:
    """Skill enriched with semantic knowledge."""

    skill_id: str
    yaml_definition: dict            # Original YAML
    semantic_description: str        # Natural language understanding

    # Relationships
    conflicts_with: list[str]        # Other skill IDs
    combines_with: list[str]         # Synergistic skills
    patterns_used: list[str]         # Design patterns

    # Issues and notes
    known_issues: list[str]
    usage_notes: list[str]

    # Embeddings for search
    embedding: list[float]
```

---

## Integration Points

### With CLI Agent

```python
# In CLI agent's decision flow
async def propose_decision(decision: Decision):
    # Check with Repo Agent first
    response = await repo_agent.verify(decision)

    if response.type == "challenge":
        print(f"Repo Agent challenges: {response.concern}")
        if not await user_confirms():
            return

    if response.type == "context":
        print(f"Repo Agent notes: {response.precedents}")

    # Proceed with decision
    await execute_decision(decision)
```

### With AI Arena

```python
# In arena session completion
async def complete_session(session: ArenaSession):
    # Enforce all agents responded
    repo_agent = get_repo_agent(session.project_id)

    missing = repo_agent.get_missing_agents(session)
    if missing:
        for agent in missing:
            await retry_agent(agent, session)

        if still_missing:
            session.status = "incomplete"
            session.missing_agents = still_missing
            await alert_user(f"Session incomplete: {still_missing}")

    # Capture knowledge
    await repo_agent.capture_session(session)
```

### With Hooks

```yaml
# .claude/hooks/knowledge-capture.yaml
hooks:
  on_conversation_end:
    - action: repo_agent.capture
      always: true

  on_arena_session:
    - action: repo_agent.enforce_completion
      block_until_complete: true
    - action: repo_agent.capture_consensus
      always: true

  on_skill_changed:
    - action: repo_agent.reindex_skill
      always: true

  on_decision_proposed:
    - action: repo_agent.verify
      may_block: true
```

---

## Enforcement Mechanisms

| Gap | Enforcement |
|-----|-------------|
| Arena agents don't all respond | Block session completion until all respond or timeout |
| Arena insights not captured | Hook runs automatically, creates memory claims |
| Skills not indexed | Skills scanned on change, auto-indexed to KB |
| Decisions not recorded | Decision proposals logged with rationale |
| Conflicts not detected | Real-time check on every skill resolution |

---

## Open Questions

1. **Persistence**: SQLite + ChromaDB? Or use CC4's existing DB?
2. **Scope**: One Repo Agent per repo? Per project? Global?
3. **Authority**: Can Repo Agent block decisions? Or only advise?
4. **Update frequency**: Real-time? On-demand? Scheduled?
5. **Multi-repo**: When CC4 splits into 4 services, how do Repo Agents coordinate?

---

## Implementation Priority

### Phase 1: Knowledge Capture
- Hook for arena session completion
- Extract entities/decisions from messages
- Store in memory_claims + KB vectors

### Phase 2: Skills as Knowledge
- Scan skills on change
- Index with semantic enrichment
- Detect conflicts

### Phase 3: Bidirectional Communication
- MCP server for Repo Agent
- CLI agent integration
- Inner Council protocol

### Phase 4: Proactive Verification
- Decision proposal hooks
- Conflict checking
- Precedent lookup

---

*"The Repo Agent is the institutional memory that no one has to maintain."*
