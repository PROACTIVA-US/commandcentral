# Hybrid Context Model: Multi-Source Project Context

> **Date:** 2026-02-01
> **Status:** Design (validated in CC4)
> **Source:** CC4 implementation analysis + session conversation
> **Priority:** Core Architecture

---

## Overview

CommandCentral uses a **hybrid context model** where project context can come from multiple sources, with intelligent caching for offline/mobile scenarios. This enables:

- Full functionality when repo is accessible (desktop with local clone)
- Degraded but functional operation offline or on mobile
- Projects without repos (pure ideation, strategy planning)

---

## Context Hierarchy

```
Context Assembly (highest to lowest priority):
┌─────────────────────────────────────────────────────────────┐
│ 4. Active Documents (pinned files from repo)                │  ← Always in context
├─────────────────────────────────────────────────────────────┤
│ 3. Repo Context (AGENTS.md, CLAUDE.md, architecture docs)   │  ← If repo accessible
├─────────────────────────────────────────────────────────────┤
│ 2. Living Context (AI-synthesized project memory in DB)     │  ← Always available
├─────────────────────────────────────────────────────────────┤
│ 1. User Defaults (global preferences, cross-project)        │  ← Baseline
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. Living Context (DB-stored, always available)

```python
class Project(Base):
    living_context = Column(Text, nullable=True)  # AI-maintained project memory
```

**Characteristics:**
- Stored in database, not filesystem
- AI-generated summary of project (under 600 words)
- Available offline, on mobile, without repo access
- Regeneratable from repo when connected

**Generation Process:**
1. On project creation, read key files from repo:
   - `CLAUDE.md` (4000 char limit)
   - `AGENTS.md` (2000 char limit)
   - Architecture docs, README, config files
2. Use Claude to synthesize into concise "project memory"
3. Store in `living_context` field
4. Regenerate on demand via `regenerate_living_context()`

### 2. Active Documents (Pinned files)

```python
class ActiveDocument(Base):
    project_id = Column(UUID)
    path = Column(String)           # Relative to repo_path
    cached_content = Column(Text)   # Cached for offline
    token_count = Column(Integer)   # For context management
    pinned_at = Column(DateTime)
```

**Characteristics:**
- Explicit user-pinned files
- Content cached in DB for offline access
- Always included in agent context
- Token-counted for context window management

### 3. Repo Context (Live, when accessible)

When repo is accessible, directly read:
- `AGENTS.md` / `CLAUDE.md` - Project instructions
- Architecture docs - Design decisions
- README - Project overview

**Freshness:** Live read from filesystem, always current.

### 4. RAG Context (KnowledgeBeast)

Semantic search across indexed project knowledge:
- Documents, code, decisions
- Retrieved based on query relevance
- Complements static context with dynamic retrieval

---

## Operating Modes

### Desktop with Local Repo (Full Mode)

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│ Context Assembly                        │
│                                         │
│  ✓ Live AGENTS.md from repo             │
│  ✓ Active Documents (cached + fresh)    │
│  ✓ Living Context (backup)              │
│  ✓ RAG from KnowledgeBeast              │
│  ✓ Skills injection                     │
└─────────────────────────────────────────┘
    │
    ▼
  Full context, always fresh
```

### Mobile / Offline (Degraded Mode)

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│ Context Assembly                        │
│                                         │
│  ✗ No repo access                       │
│  ✓ Active Documents (from cache)        │
│  ✓ Living Context (from DB)             │
│  ~ RAG (if KB is accessible)            │
│  ✓ Skills injection                     │
└─────────────────────────────────────────┘
    │
    ▼
  Functional context, may be stale
```

### No-Repo Projects (Ideation Mode)

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│ Context Assembly                        │
│                                         │
│  n/a No repo configured                 │
│  ✓ Manual Active Documents              │
│  ✓ Living Context (user-edited)         │
│  ✓ RAG from KnowledgeBeast              │
│  ✓ Skills injection                     │
└─────────────────────────────────────────┘
    │
    ▼
  Context from DB only, fully functional
```

---

## Sync Strategy

### Repo → Living Context

```
Trigger: Project creation, manual refresh, or scheduled sync

1. Read priority files from repo:
   - CLAUDE.md (4000 chars)
   - AGENTS.md (2000 chars)
   - docs/plans/master.md (3000 chars)
   - Architecture docs, README, configs

2. Synthesize with Claude:
   "Create a concise project memory document (under 600 words)
    that captures the essence of this project..."

3. Store result in project.living_context

4. Update last_synced timestamp
```

### Active Document Refresh

```
Trigger: Document pinned, manual refresh, or file change detected

1. Read file content from repo_path + path
2. Count tokens
3. Update cached_content and token_count
4. Mark refresh timestamp
```

---

## Mobile Considerations

### GitHub API Fallback

When no local repo but GitHub remote configured:

```python
async def fetch_agents_md_from_github(project: Project) -> str | None:
    """Fetch AGENTS.md via GitHub API when local repo unavailable."""

    if not project.github_repo:
        return None

    # Use GitHub MCP or API
    content = await github_api.get_file_contents(
        owner=project.github_owner,
        repo=project.github_repo,
        path="AGENTS.md"
    )

    return content
```

### Staleness Indicators

```python
class ContextFreshness:
    source: Literal["live", "cached", "synthesized"]
    last_synced: datetime
    is_stale: bool  # > 24 hours since sync

    def get_warning(self) -> str | None:
        if self.is_stale:
            return f"Context last synced {humanize(self.last_synced)}"
        return None
```

---

## Implementation in CommandCentral

### Project Model Extension

```python
class Project(Base):
    # Existing
    repo_path = Column(String)
    living_context = Column(Text)

    # New for hybrid model
    github_repo = Column(String, nullable=True)      # owner/repo
    context_last_synced = Column(DateTime)
    context_source = Column(String)                  # "repo", "github", "manual"
```

### Context Service

```python
class ProjectContextService:
    """Manages hybrid context assembly."""

    async def get_context(self, project_id: UUID) -> AssembledContext:
        """Get best available context for project."""

        project = await self.get_project(project_id)

        # Try sources in priority order
        if self._can_access_repo(project):
            return await self._context_from_repo(project)

        if project.github_repo and self._is_online():
            return await self._context_from_github(project)

        # Fallback to cached/synthesized
        return self._context_from_db(project)

    async def sync_context(self, project_id: UUID) -> SyncResult:
        """Refresh living_context from repo."""
        ...
```

---

## Benefits

1. **Resilience** - Works offline, on mobile, without repo
2. **Freshness** - Live repo read when available
3. **Flexibility** - Projects without repos still work
4. **Efficiency** - Synthesized context is token-optimized
5. **Consistency** - Same mental model across all platforms

---

## Open Questions

1. **Conflict resolution** - What if living_context diverges significantly from repo?
2. **Sync frequency** - Auto-sync on session start? Scheduled? Manual only?
3. **Mobile GitHub auth** - OAuth flow for private repos on mobile?
4. **Staleness threshold** - How old before warning user?

---

*"The repo is the source of truth, but the DB is the source of availability."*
