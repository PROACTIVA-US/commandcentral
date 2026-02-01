---
title: CommandCentral Master Plan
type: plan
status: active
created: 2026-02-01
updated: 2026-02-01 12:45
owner: daniel
tags: [commandcentral, architecture, roadmap]
progress: 15
---

# CommandCentral Master Plan

## Executive Summary

CommandCentral is the governance and coordination hub for a microservices ecosystem. It provides unified navigation, AI Arena for multi-model deliberation, project federation, and knowledge management. Development continues in CommandCentral while using CC4's running backend for Arena and KnowledgeBeast.

---

## Current State

### Infrastructure (Working)

| Component | Location | Status |
|-----------|----------|--------|
| CC4 Backend | localhost:8001 | Running - 140+ endpoints |
| KnowledgeBeast | CC4 | Running - 44+ documents indexed |
| Arena API | CC4 | Working - preflight + chat verified |
| Skills | CommandCentral/skills/ | 63 files ported, indexed in KB |
| The Vine CLI | /Projects/Wildvine/the-vine/ | Pipeline framework working (LLM TODO) |

### Architecture Docs (Completed)

| Document | Purpose |
|----------|---------|
| `intent-enforcement.md` | FAIL_LOUD default, pre-flight mandatory |
| `pipeline-architecture.md` | Universal Pipeline → Stage → Executor model |
| `skills-as-knowledge.md` | Skills indexed for semantic discovery |
| `repo-agent-design.md` | Persistent agent with knowledge capture |
| `product-vision-clarity.md` | Wildvine Labs vs Network vs The Vine |
| `project-federation.md` | Multi-project hub with Tech Radar |

---

## Architectural Principles

1. **Intent Is Sacred** - FAIL_LOUD default, never silently work around
2. **Everything Is a Pipeline** - Universal Input → Stages → Output model
3. **Skills as Knowledge** - Semantic discovery, conflict detection
4. **No Silent Workarounds** - Report failures, don't hide them
5. **Knowledge Capture** - Never lose insights from sessions
6. **Project Federation** - CC as hub, bidirectional improvement sharing

---

## Development Priorities

Based on Arena consensus (Claude, GPT, Grok all agreed):

### Priority 1: Production Hardening & Reliability

- [ ] Error handling and graceful degradation
- [ ] Logging, monitoring, observability
- [ ] Automated testing for critical paths
- [ ] CI/CD gates, rollback strategy

### Priority 2: User Experience & Feedback Loop

- [ ] Workflow simplification
- [ ] Response quality improvements
- [ ] Feedback mechanisms (ratings, issue reporting)
- [ ] User-facing documentation

### Priority 3: Extensibility & Governance

- [ ] Stable APIs for integrations
- [ ] Skill/plugin development framework
- [ ] Security & multi-user support
- [ ] Knowledge lifecycle management

---

## Frontend Build Plan

### Tech Stack
- React 18 + TypeScript + Vite
- Tailwind CSS + shadcn/ui
- Zustand + TanStack Query
- React Router v6 + @xyflow/react

### Backend Services

| Service | Port | Responsibility |
|---------|------|----------------|
| CommandCentral | 8000 | Auth, projects, decisions, audit, AI Arena |
| PIPELZR | 8001 | Tasks, pipelines, agents, skills |
| VISLZR | 8002 | Canvas, nodes, visualization |
| IDEALZR | 8003 | Goals, hypotheses, evidence |

### Build Phases

**Phase 1: Foundation** (Batches 1-2)
- Vite + React + TypeScript setup
- Tailwind + shadcn/ui configuration
- Base API client with JWT
- Zustand stores (auth, ui, project)
- AppShell, Header, TabNavigation
- React Router configuration

**Phase 2: Core Features** (Batches 3-5)
- Authentication (login, register, protected routes)
- Dashboard with cross-service stats
- Service tabs (IDEALZR, PIPELZR, VISLZR, Governance)
- AI Arena integration

**Phase 3: Polish** (Batches 6-7)
- Global search (Cmd+K)
- Notifications with WebSocket
- Settings and profile
- Loading states, error boundaries, dark mode

### Frontend Additions Needed

1. **AI Arena Feature**
   - Arena page under Governance tab
   - Session list, create session
   - Multi-agent chat view
   - Preflight check UI
   - Knowledge capture display

2. **Project Registry** (Future)
   - View connected projects
   - Initialize new project wizard
   - Improvement notifications

---

## Project Federation (Future Phase)

### Concept
CommandCentral as hub for multiple projects using its core infrastructure.

### KB Model
Explicit sync - each project owns its KB, copies selected knowledge from CC.

### Project Initialization Flow
1. Scan project repo
2. Configure governance (allowed/blocked actions)
3. Configure constitution (principles, intent enforcement)
4. Select skills to share
5. Select knowledge to sync

### Tech Radar Pipeline (Self-Improvement)
```
SCAN (Cron) → EVALUATE (Score) → PLAN → TEST (Sandbox) → NOTIFY → APPROVE → DISTRIBUTE
```

### Bidirectional Communication
- CC → Projects: Push improvements (firmware-style)
- Projects → CC: Report discoveries
- Security testing mandatory before any improvement approved

---

## Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| KB Model | Explicit sync | Projects own their KB, copy from CC |
| CC4 Usage | Backend only | Use CC4's running backend from CommandCentral |
| AI Arena | In CommandCentral | Fits governance/decision-making role |
| Skills | Local ownership | Each service owns skills, indexed centrally |
| Execution | CC4 short-term | Migrate to PIPELZR long-term |

---

## File Structure

```
CommandCentral/
├── docs/
│   ├── MASTER-PLAN.md          # This file - single source of truth
│   ├── architecture/
│   │   ├── active/             # Living architecture docs (6 files)
│   │   └── decisions/          # Architecture decision records
│   ├── specs/
│   │   └── commandcentral-frontend.md  # Frontend build spec
│   ├── service-spec/           # Self-documentation
│   └── standards/              # Specs for skills, pipelines, docs
├── skills/                     # 63 skill files (12 active, 46 archived)
├── scripts/                    # Utility scripts
└── frontend/                   # React frontend (to be built)
```

---

## Quick Reference

### Start CC4 Backend
```bash
cd /Projects/CC4
source backend/.venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

### Test Arena
```bash
# Preflight check
curl -s http://localhost:8001/api/v1/arena/preflight/flagship-models

# Create session
curl -X POST http://localhost:8001/api/v1/arena/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Session"}'
```

### Test The Vine
```bash
cd /Projects/Wildvine/the-vine
source .venv/bin/activate
vine status
vine preflight
```

### Search KB
```bash
curl -X POST http://localhost:8001/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "your search query"}'
```

---

## Next Actions

1. **Build Frontend Phase 1** - Foundation (Batches 1-2 from spec)
2. **Add AI Arena to Frontend** - Update spec, implement feature
3. **Production Hardening** - Error handling, logging, testing
4. **Documentation** - User guides, not just architecture

---

*"Architecture is clear. Infrastructure exists. Time to execute."*
