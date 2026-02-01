---
name: agent-native-architecture
description: Build AI agents using prompt-native architecture where features are defined in prompts, not code. Use when creating autonomous agents, designing MCP servers, implementing self-modifying systems, or adopting the "trust the agent's intelligence" philosophy.
category: architecture
keywords:
  - agent-native
  - prompt-native
  - autonomous
  - orchestration
  - primitives
  - self-improvement
---

# Agent-Native Architecture

Build systems where **agents figure out HOW**, not just WHAT.

## Core Principle

> **Whatever a user can do, an agent can do. Whatever a user can see, an agent can see.**

Features should be defined in prompts (data), not code (logic). The agent's intelligence handles the "how".

## The Cardinal Sin

```python
# BAD - Developer decides how agent works
def _select_model(self, task) -> str:
    if complexity == "simple": return "haiku"
    elif complexity == "complex": return "opus"
    else: return "sonnet"

# GOOD - Agent decides how agent works
result = await orchestrator_agent.run(
    prompt=f"Configure agent for task: {task}. Choose model, tools, approach."
)
```

**Rule**: If you're writing `if/else` logic to decide agent behavior, you're doing it wrong.

## Agent-Native vs Traditional

| Aspect | Traditional | Agent-Native |
|--------|-------------|--------------|
| Model selection | Code picks model | Agent picks model |
| Tool grants | Pre-computed by algorithm | Agent requests what it needs |
| Execution order | Fixed pipeline stages | Agent determines workflow |
| Error handling | Pattern matching | Agent analyzes and decides |
| Learning | Predefined hooks | Agent identifies learnings |
| Memory | Injected context | Agent queries what it needs |

## Anti-Patterns to Avoid

### 1. Hardcoded Workflows

```python
# ANTI-PATTERN: Fixed extraction approach
async def extract_tasks(spec: str) -> list[Task]:
    prompt = f"Extract tasks from: {spec}"  # Fixed prompt
    return await call_claude(prompt)

# AGENT-NATIVE: Agent decides extraction approach
async def extract_tasks(spec: str) -> list[Task]:
    return await extraction_agent.run(
        prompt=f"Understand this spec and extract actionable tasks: {spec}"
    )
```

### 2. Artificial Limits

```python
# ANTI-PATTERN: Hardcoded forbidden actions
forbidden_actions = ["delete_database", "modify_auth"]

# AGENT-NATIVE: Agent has user's permissions
agent_capabilities = user.get_capabilities()
```

If a user can do it, the agent should be able to (with appropriate safeguards).

### 3. Pre-injected Context

```python
# ANTI-PATTERN: Developer decides what context to inject
memory_context = self.memory.load_context(project_id)
enhanced_prompt = f"{task}\n\nContext: {memory_context}"

# AGENT-NATIVE: Agent queries for context it needs
# Agent has access to: query_memory(question: str) -> str
```

### 4. Pattern-Based Triage

```python
# ANTI-PATTERN: Regex patterns for failure handling
TRANSIENT_PATTERNS = [
    (r"timeout|timed out", "timeout"),
    (r"rate.?limit|429", "rate_limit"),
]

# AGENT-NATIVE: Agent analyzes failures
triage_result = await triage_agent.run(
    prompt=f"Analyze this failure and recommend recovery: {error}"
)
```

### 5. Fixed Pipeline Stages

```python
# ANTI-PATTERN: Hardcoded phase guidance
PHASES = ["discover", "validate", "improve"]
def get_phase_guidance(phase: str) -> str:
    return PHASE_PROMPTS[phase]

# AGENT-NATIVE: Agent determines its own approach
# No phases - agent works until task is complete
```

## Required Primitives

For agents to be truly autonomous, expose these as tools:

### Memory Primitives

```python
@tool
async def query_memory(question: str) -> str:
    """Ask any question about project history, decisions, knowledge."""

@tool
async def search_episodes(query: str, filters: dict = None) -> list[Episode]:
    """Search past events matching criteria."""

@tool
async def recall_knowledge(topic: str) -> list[Knowledge]:
    """Recall stored knowledge about a topic."""
```

### File Primitives

```python
@tool
async def search_codebase(query: str, pattern: str = "**/*") -> list[str]:
    """Search for files or content matching query."""

@tool
async def explore_directory(path: str) -> dict:
    """Get structure of directory."""
```

### Self-Modification Primitives

```python
@tool
async def propose_skill_update(skill_slug: str, learning: str) -> bool:
    """Propose an update to a skill based on new learning."""

@tool
async def create_skill(name: str, content: str) -> Skill:
    """Create a new skill from discovered knowledge."""
```

### Resource Primitives

```python
@tool
async def check_budget() -> dict:
    """Check remaining API budget and token limits."""

@tool
async def request_capability(capability: str, reason: str) -> bool:
    """Request additional capabilities with justification."""
```

## Implementation Checklist

When building agent systems, verify:

### Configuration
- [ ] Model selection is agent-driven, not algorithmic
- [ ] Tool grants are requested by agent, not pre-computed
- [ ] No hardcoded forbidden actions (use permission system instead)
- [ ] No artificial limits on skill injection, memory tokens, etc.

### Memory
- [ ] Agent can QUERY memory, not just receive injected context
- [ ] Agent can search episodes with filters
- [ ] Agent can recall knowledge by topic
- [ ] Agent decides what context it needs

### Workflows
- [ ] No fixed pipeline stages
- [ ] No phase-specific guidance that constrains behavior
- [ ] Agent determines its own execution approach
- [ ] Agent can modify its workflow mid-execution

### Error Handling
- [ ] Triage is agent-driven, not pattern-matching
- [ ] Agent analyzes failures and recommends recovery
- [ ] No hardcoded retry counts or escalation thresholds

### Learning
- [ ] Agent identifies what's worth learning
- [ ] Agent can propose skill updates
- [ ] Agent can create new skills
- [ ] Learning points are not predefined by developer

## Migration Path

To convert existing code to agent-native:

1. **Identify hardcoded logic** - Find `if/else` that decides agent behavior
2. **Convert to prompts** - Replace logic with agent queries
3. **Expose primitives** - Give agents tools to query what they need
4. **Remove constraints** - Eliminate artificial limits
5. **Trust the agent** - Let it determine its approach

## When NOT to Use Agent-Native

Some things should remain deterministic:

- **Security boundaries** - Permission checks, authentication
- **Data integrity** - Transaction handling, consistency guarantees
- **Audit logging** - Compliance requirements
- **Rate limiting** - External API constraints

These are infrastructure concerns, not agent behavior decisions.

## Testing Agent-Native Systems

```python
# Test that agent CAN do what users can do
async def test_agent_has_user_capabilities():
    user_actions = get_user_available_actions()
    agent_tools = get_agent_available_tools()
    assert set(user_actions) <= set(agent_tools)

# Test that agent determines its own approach
async def test_agent_self_configures():
    result = await agent.run("Complex analysis task")
    assert result.model_used is not None  # Agent chose
    assert result.tools_used is not None  # Agent chose
```

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `autonomy` | HOW agents persist (Ralph loops) |
| `damage-control` | Safety guardrails for agent operations |
| `rlm-decomposition` | Agent-native approach to complex reasoning |

---

*Features in prompts, not code. Trust the agent's intelligence.*
