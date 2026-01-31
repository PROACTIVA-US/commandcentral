# Session Handoff: Wildvine → CommandCentral Architecture

> **Date:** 2026-01-31
> **From Session:** Wildvine exploration and architecture review
> **To Session:** CommandCentral implementation
> **Status:** Ready for implementation

---

## Executive Summary

This session started as a Wildvine review but evolved into critical architectural insights for the entire ecosystem. Key outputs:

1. **Product vision clarity** - Clarified relationship between Wildvine Labs, Wildvine Network, and The Vine
2. **Repo Agent design** - Persistent, conversational agent with bidirectional communication
3. **Pipeline architecture** - Universal model where everything is a pipeline
4. **Intent enforcement** - No silent workarounds, ever
5. **Skills as knowledge** - Unique approach to making skills discoverable and combinable
6. **AI Arena gaps** - Investigation revealing missing Kimi, no knowledge capture

---

## Documents Created

### In CommandCentral (`/docs/architecture/`)

| Document | Purpose |
|----------|---------|
| `product-vision-clarity.md` | Clarifies The Vine vs Wildvine Labs vs Wildvine Network |
| `repo-agent-design.md` | Design for persistent repo agent with Inner Council |
| `pipeline-architecture.md` | Universal pipeline model for all services |
| `intent-enforcement.md` | No silent workarounds, pre-flight checks mandatory |
| `skills-as-knowledge.md` | Skills as searchable, combinable knowledge |
| `ai-arena-gaps-and-fixes.md` | Investigation + fixes for arena issues |

### In Wildvine (`/docs/`)

| Document | Purpose |
|----------|---------|
| `repo-agent-design.md` | Original design (copied to CommandCentral) |
| `pipeline-architecture.md` | Original design (copied to CommandCentral) |

---

## Key Insights

### 1. The Vine vs AI Arena

| AI Arena | The Vine |
|----------|----------|
| Agents **debate** a topic | Agents **generate and refine ideas** |
| Produces consensus | Produces product concepts |
| Fixed rounds | Flexible steering |
| Internal knowledge only | External research (web, YouTube, X) |

**The Vine is for product ideation.** It's a distinct product with vertical-specific positioning potential.

### 2. Everything Is a Pipeline

These are all pipelines:
- AI Arena
- UX/UI Validation
- Knowledge Radar
- Idea → Hypothesis → Execute
- The Vine (agent ideation)
- Principle Garden

All should use the same `Pipeline → Stage → Executor` model with:
- Pre-flight checks
- Failure policies
- Self-reconfiguration
- Visualization

### 3. Intent Is Sacred

**Problem discovered:** Kimi was configured but silently skipped. A workaround session was created without telling the user.

**Fix:** `FailurePolicy.FAIL_LOUD` as default. No silent workarounds. If the user configured 4 agents, all 4 must participate or the system fails loudly.

### 4. Knowledge Must Be Captured

**Problem discovered:** Arena session produced 6 substantive responses. Zero memory claims created. Knowledge lost.

**Fix:** Mandatory knowledge capture hook on every arena session end. Extract entities, decisions, consensus → store as memory claims.

### 5. Skills as Knowledge (Unique Approach)

Most systems: Skills are static YAML config.

Our approach: Skills are indexed as knowledge with:
- Semantic descriptions (for discovery)
- Conflict relationships (for safety)
- Combination suggestions (for guidance)
- Known issues (for awareness)

This enables semantic skill discovery: "find skills for user identity" instead of exact trigger matching.

---

## Investigation Findings

### AI Arena Session Analysis

**Configured:** Claude, GPT, Grok, Kimi
**Actually ran:** Claude, GPT, Grok (NO KIMI)

**Sessions with Kimi configured:** 0 messages produced
**Session without Kimi:** 6 messages produced

**Conclusion:** Workaround session was created silently. User intent violated.

### Moonshot/Kimi Status

- API key IS configured: `MOONSHOT_API_KEY=sk-CJ6...`
- Provider IS implemented in `llm_provider.py`
- Something failed but was silently handled

---

## Implementation Priorities

### Immediate (AI Arena)

1. Add pre-flight check before arena sessions
2. Block session start if any required agent fails preflight
3. Never create alternative sessions without failing agents
4. Report failures clearly with actionable options

### Short-term (Knowledge Capture)

5. Add knowledge capture hook to arena session end
6. Extract entities, decisions, consensus from messages
7. Create memory claims with provenance
8. Index to KnowledgeBeast

### Medium-term (Pipeline Model)

9. Define universal Pipeline/Stage/Config model
10. Migrate AI Arena to pipeline model
11. Add self-reconfiguration (extend UX pipeline pattern)
12. Build pipeline visualization

### Long-term (Repo Agent)

13. Implement Repo Agent as MCP server
14. Add bidirectional communication with CLI agent
15. Implement Inner Council protocol
16. Enable proactive verification

---

## Open Questions (For Next Session)

1. **Pipeline Registry Location:** Central (CommandCentral) or per-service?
2. **Repo Agent Scope:** Per repo? Per project? Global?
3. **Cross-Service Pipelines:** Can pipelines span CC4 + Wildvine + The Vine?
4. **The Vine MVP:** Should we build The Vine before fixing Arena?

---

## Files to Review

1. `/Users/danielconnolly/Projects/CommandCentral/docs/architecture/` - All new docs
2. `/Users/danielconnolly/Projects/CC4/backend/app/services/llm_provider.py` - Moonshot integration
3. `/Users/danielconnolly/Projects/CC4/backend/data/cc4.db` - Arena tables
4. `/Users/danielconnolly/Projects/Wildvine/docs/spec.md` - Wildvine spec

---

## Next Session Recommendations

1. **Start with arena pre-flight** - Quickest win, prevents future issues
2. **Then knowledge capture** - Prevents insight loss
3. **Then pipeline model** - Foundation for everything else
4. **Return to Wildvine** - Continue original work with new infrastructure

---

## Summary

This session produced critical infrastructure designs that apply across all services. The key principle: **User intent is sacred. Never work around problems silently.** All pipelines, agents, and processes should enforce this.

Documents are now in CommandCentral for implementation. Wildvine work can continue with these foundations in place.

---

*"Build it simple. Leave gaps. See what emerges. But never silently violate user intent."*
