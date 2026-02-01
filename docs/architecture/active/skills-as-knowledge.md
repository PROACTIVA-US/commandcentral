# Skills as Knowledge: A Unique Approach

> **Date:** 2026-01-31
> **Status:** Design Draft
> **Source:** Wildvine session conversation + AI Arena review
> **Note:** This approach is significantly different from how most systems handle skills

---

## The Insight

Most systems treat skills as **static configuration**:
- YAML files in a directory
- Loaded at startup
- Matched by triggers/patterns
- Used as instructions

This misses the opportunity for skills to be:
- **Discoverable** semantically ("find skills that handle user identity")
- **Combinable** intelligently (know which skills work together)
- **Conflict-aware** (detect when two skills clash)
- **Learnable** (agents understand skills deeply, not just follow them)

---

## Current State vs. Target

### Current: Skills as Config

```yaml
# /docs/service-spec/skills/auth-flow.yaml
id: auth-flow
name: "Authentication Flow"
triggers:
  - "login"
  - "auth"
  - "oauth"
instructions: |
  When handling authentication:
  1. Check if user exists
  2. Validate credentials
  3. Issue JWT token
```

**Limitations:**
- Matched only by exact triggers
- No semantic understanding
- No conflict detection
- No composition guidance

### Target: Skills as Knowledge

```yaml
# /docs/service-spec/skills/auth-flow.yaml
id: auth-flow
name: "Authentication Flow"
triggers:
  - "login"
  - "auth"
  - "oauth"
instructions: |
  When handling authentication:
  1. Check if user exists
  2. Validate credentials
  3. Issue JWT token

# NEW: Knowledge enrichment
knowledge:
  semantic_description: |
    Handles user authentication including OAuth providers.
    Uses JWT tokens for session management.
    Requires HTTPS in production environments.
    Compatible with both browser and API clients.

  relationships:
    conflicts_with:
      - basic-auth-skill
      - session-cookie-auth
    combines_with:
      - session-management
      - user-profile
      - permission-checking
    requires:
      - database-access
      - crypto-utils

  patterns_used:
    - "token-based-auth"
    - "provider-agnostic-oauth"
    - "refresh-token-rotation"

  known_issues:
    - "Token refresh race condition in concurrent requests (see issue #234)"
    - "OAuth callback URL must be registered per environment"

  usage_notes:
    - "Always validate token expiry before trusting claims"
    - "Store refresh tokens securely, never in localStorage"
```

---

## What This Enables

### 1. Semantic Skill Discovery

Instead of exact trigger matching:

```python
# OLD: Exact match
skills = registry.match_triggers("login")  # Only finds skills with "login" trigger

# NEW: Semantic search
skills = kb.search("find skills that handle user identity verification")
# Finds: auth-flow, user-profile, permission-checking, etc.
```

### 2. Conflict Detection

```python
async def resolve_skills(task: str) -> list[Skill]:
    candidates = await kb.search(task)

    # Check for conflicts
    for i, skill_a in enumerate(candidates):
        for skill_b in candidates[i+1:]:
            if skill_a.id in skill_b.conflicts_with:
                raise SkillConflict(
                    f"Cannot use both {skill_a.name} and {skill_b.name}: "
                    f"they conflict on authentication approach"
                )

    return candidates
```

### 3. Composition Suggestions

```python
async def suggest_skill_additions(selected: list[Skill]) -> list[Skill]:
    suggestions = []

    for skill in selected:
        for combo_id in skill.combines_with:
            combo_skill = await registry.get(combo_id)
            if combo_skill not in selected:
                suggestions.append(SuggestionItem(
                    skill=combo_skill,
                    reason=f"Often used with {skill.name}"
                ))

    return suggestions
```

### 4. Dependency Checking

```python
async def check_dependencies(skill: Skill) -> DependencyResult:
    missing = []

    for required_id in skill.requires:
        if not await registry.has(required_id):
            missing.append(required_id)

    if missing:
        return DependencyResult(
            satisfied=False,
            missing=missing,
            message=f"{skill.name} requires: {', '.join(missing)}"
        )

    return DependencyResult(satisfied=True)
```

---

## Indexing Skills in KnowledgeBeast

Skills get indexed just like any other knowledge:

```python
async def index_skill(skill: Skill):
    """Index skill into KnowledgeBeast for semantic search."""

    # Combine all text for embedding
    full_text = f"""
    Skill: {skill.name}

    Description: {skill.knowledge.semantic_description}

    Triggers: {', '.join(skill.triggers)}

    Works with: {', '.join(skill.knowledge.relationships.combines_with)}

    Conflicts with: {', '.join(skill.knowledge.relationships.conflicts_with)}

    Patterns: {', '.join(skill.knowledge.patterns_used)}

    Known issues: {chr(10).join(skill.knowledge.known_issues)}

    Usage notes: {chr(10).join(skill.knowledge.usage_notes)}
    """

    # Create embedding
    embedding = await embeddings.embed(full_text)

    # Index in KB
    await kb.index(
        id=f"skill:{skill.id}",
        content=full_text,
        embedding=embedding,
        metadata={
            "type": "skill",
            "skill_id": skill.id,
            "conflicts_with": skill.knowledge.relationships.conflicts_with,
            "combines_with": skill.knowledge.relationships.combines_with,
            "requires": skill.knowledge.relationships.requires,
        }
    )
```

---

## Auto-Reindexing on Change

When skills change, automatically reindex:

```python
class SkillWatcher:
    """Watch for skill changes and reindex."""

    def __init__(self, skill_dir: Path, kb: KnowledgeBeast):
        self.skill_dir = skill_dir
        self.kb = kb

    async def watch(self):
        """Watch skill directory for changes."""
        async for change in watchfiles.awatch(self.skill_dir):
            for change_type, path in change:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    await self.handle_change(change_type, path)

    async def handle_change(self, change_type: str, path: str):
        skill_id = Path(path).stem

        if change_type == 'deleted':
            await self.kb.delete(f"skill:{skill_id}")
            logger.info(f"Skill {skill_id} removed from KB")

        else:  # added or modified
            skill = await load_skill(path)
            await index_skill(skill)
            logger.info(f"Skill {skill_id} indexed to KB")

            # Check for new conflicts
            conflicts = await self.detect_new_conflicts(skill)
            if conflicts:
                await self.notify_conflicts(skill, conflicts)
```

---

## Skill Knowledge Data Model

```python
@dataclass
class SkillKnowledge:
    """Knowledge enrichment for a skill."""

    semantic_description: str
    # Natural language description of what the skill does
    # Used for semantic search

    relationships: SkillRelationships
    # Conflicts, combinations, dependencies

    patterns_used: list[str]
    # Design patterns this skill implements

    known_issues: list[str]
    # Known problems and workarounds

    usage_notes: list[str]
    # Tips for using this skill effectively

@dataclass
class SkillRelationships:
    """How this skill relates to others."""

    conflicts_with: list[str]
    # Skill IDs that cannot be used together

    combines_with: list[str]
    # Skill IDs that work well together

    requires: list[str]
    # Skill IDs that must be present

    supersedes: list[str]
    # Skill IDs that this skill replaces

@dataclass
class Skill:
    """Complete skill definition."""

    # Core (existing)
    id: str
    name: str
    triggers: list[str]
    instructions: str

    # Knowledge enrichment (new)
    knowledge: SkillKnowledge

    # Metadata
    version: str
    last_updated: datetime
    embedding: list[float]  # For KB search
```

---

## Integration with Repo Agent

The Repo Agent uses skills as knowledge:

```python
class RepoAgent:
    """Uses skill knowledge for decision support."""

    async def verify_skill_usage(self, proposed_skills: list[str]) -> Verification:
        """Verify proposed skill combination is valid."""

        # Check conflicts
        for skill_id in proposed_skills:
            skill = await self.skill_registry.get(skill_id)
            for other_id in proposed_skills:
                if other_id in skill.knowledge.relationships.conflicts_with:
                    return Verification(
                        valid=False,
                        issue=f"{skill_id} conflicts with {other_id}",
                        suggestion=f"Choose one: {skill_id} OR {other_id}"
                    )

        # Check dependencies
        for skill_id in proposed_skills:
            skill = await self.skill_registry.get(skill_id)
            for required_id in skill.knowledge.relationships.requires:
                if required_id not in proposed_skills:
                    return Verification(
                        valid=False,
                        issue=f"{skill_id} requires {required_id}",
                        suggestion=f"Add {required_id} to your skill selection"
                    )

        # Suggest additions
        suggestions = await self.suggest_additions(proposed_skills)

        return Verification(
            valid=True,
            suggestions=suggestions
        )
```

---

## Migration Path

### Phase 1: Add Knowledge to Existing Skills

```bash
# For each skill in /docs/service-spec/skills/
for skill in *.yaml:
    # Add knowledge section
    add_knowledge_template(skill)
    # Human reviews and enriches
done
```

### Phase 2: Index Skills to KB

```python
# One-time indexing
async def index_all_skills():
    for skill_path in skill_dir.glob("*.yaml"):
        skill = await load_skill(skill_path)
        await index_skill(skill)
```

### Phase 3: Enable Semantic Discovery

```python
# Update skill resolution to use KB
async def resolve_skills(task: str) -> list[Skill]:
    # First: semantic search in KB
    kb_results = await kb.search(task, type="skill")

    # Then: traditional trigger matching
    trigger_results = await trigger_match(task)

    # Combine and rank
    return combine_and_rank(kb_results, trigger_results)
```

### Phase 4: Enable Conflict Detection

```python
# Add conflict checking to pipeline execution
async def execute_pipeline(stages: list[Stage]):
    skills_to_use = collect_skills(stages)
    await verify_no_conflicts(skills_to_use)
    # ... continue
```

---

## Benefits Summary

| Capability | Before | After |
|------------|--------|-------|
| Discovery | Exact trigger match | Semantic search |
| Conflicts | Manual tracking | Automatic detection |
| Composition | Trial and error | Guided suggestions |
| Dependencies | Runtime failures | Pre-execution checks |
| Understanding | Read instructions | Deep semantic knowledge |

---

## Open Questions

1. **Authoring burden**: How to make it easy to add knowledge to skills?
2. **Validation**: How to verify relationship claims are accurate?
3. **Version drift**: What if conflicts/combinations change over time?
4. **Cross-service**: How to handle skills from different services?

---

*"Skills aren't just instructions. They're knowledge to be understood, combined, and reasoned about."*
