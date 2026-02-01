---
title: Unbuilt Features Inventory - All CommandCenter Versions
created: 2026-01-31
status: active
purpose: Comprehensive inventory of planned but unbuilt features across all CC versions
---

# Unbuilt Features Inventory

This document catalogs all features that were **planned but NOT built** across CommandCenter V1, CommandCenter 2.0, and CC4. Use this as a reference for what capabilities exist only as specs/plans.

## Executive Summary

| Project | Total Unbuilt | Critical (P0) | High (P1) | Medium (P2) |
|---------|---------------|---------------|-----------|-------------|
| CommandCenter V1 | 37+ | 9 | 12 | 16+ |
| CommandCenter 2.0 | 60+ | 5 | 10 | 45+ |
| CC4 | 50+ | 8 | 15 | 27+ |
| **Total Unique** | **100+** | - | - | - |

---

## Part 1: CommandCenter V1 Unbuilt Features

### 1.1 Async Job Execution (Celery Tasks) - STUBS ONLY

| Feature | File | Line | Status |
|---------|------|------|--------|
| Analysis Job Execution | `backend/app/tasks/analysis_tasks.py` | 8-21 | Returns `{"status": "not_implemented"}` |
| Export Job Execution | `backend/app/tasks/export_tasks.py` | 8-21 | Returns `{"status": "not_implemented"}` |
| Batch Export Job Logic | `backend/app/tasks/job_tasks.py` | 274 | TODO comment |
| Webhook Delivery Task | `backend/app/tasks/job_tasks.py` | 310 | TODO comment |
| Scheduled Analysis Task | `backend/app/tasks/job_tasks.py` | 346 | TODO comment |

### 1.2 Research Orchestration - NOT IMPLEMENTED

| Feature | File | Line | Status |
|---------|------|------|--------|
| GitHub Monitoring | `backend/app/routers/research_orchestration.py` | 420 | "Coming in Phase 2" |
| arXiv Monitoring | `backend/app/routers/research_orchestration.py` | 427 | "Coming in Phase 2" |
| Cost Calculation | `backend/app/routers/research_orchestration.py` | 530 | Hardcoded to `0.0 USD` |

### 1.3 Graph & Multi-Project Features

| Feature | File | Line | Status |
|---------|------|------|--------|
| Multi-Project Expansion | `backend/app/routers/graph.py` | 421 | TODO - hardcoded to single project |
| Multi-Project Authorization | `backend/app/routers/graph.py` | 471 | TODO |

### 1.4 Action Executor / Affordances

| Feature | File | Line | Status |
|---------|------|------|--------|
| Audit Service Integration | `backend/app/services/action_executor.py` | 109 | TODO - logs only |
| Task Service Integration | `backend/app/services/action_executor.py` | 212 | TODO |
| Indexer Service Integration | `backend/app/services/action_executor.py` | 232 | TODO |

### 1.5 Major Feature Modules (Spec Only)

| Feature | Documentation | Status |
|---------|---------------|--------|
| **Wander Engine** | `docs/ROADMAP.md:63-64` | Designed, not built |
| **MRKTZR CRM Foundation** | `docs/ROADMAP.md:26` | Planned Q1-Q2 2026 |
| **VERIA Polymarket Integration** | `docs/ROADMAP.md:27` | Planned Q1-Q2 2026 |
| **Voice Input Prototype** | `docs/ROADMAP.md:22` | Planned, not started |
| **IdeaHub Engine** | `docs/plans/2026-01-03-ideahub-spec.md` | Spec written, not implemented |
| **Phase 6: Health & Service Discovery** | `docs/plans/phase-6-health-service-discovery-plan.md` | Plan written, not implemented |
| **Global Reputation Monitoring** | `docs/global-reputation-check-automation-spec.md` | Detailed spec, not implemented |

### 1.6 Sprint Backlog (Not Started)

From `docs/plans/composable-surface-sprint-plan.md`:

| Sprint | Features | Status |
|--------|----------|--------|
| Sprint 5 | Temporal queries, Semantic search, Computed properties, NLP intent parser | Future |
| Sprint 7 | Agent Observability | Q1 2026 |
| Sprint 8 | Automated QA Pipeline | Q1 2026 |
| Sprint 9 | Task Inbox | Q1 2026 |

### 1.7 LLM Gateway Features

| Feature | File | Line | Status |
|---------|------|------|--------|
| Database-Backed Provider Config | `backend/libs/llm_gateway/providers.py` | 317 | TODO Phase 1 |
| Database Provider Registration | `backend/libs/llm_gateway/providers.py` | 358 | TODO Phase 1 |

---

## Part 2: CommandCenter 2.0 Unbuilt Features

### 2.1 Strategic Intelligence System (Spec Section 5) - CRITICAL

| Feature | Spec Location | Code Status |
|---------|---------------|-------------|
| **Wander Agent** | `docs/specs/commandcenter3.md:2655-2696` | `intelligence.py:59-65` - returns stub |
| **Source Curator** | `docs/specs/commandcenter3.md:2696-2721` | No service exists |
| **Hypothesis Engine** | `backend/app/services/hypothesis_service.py` | 3 of 4 methods raise `NotImplementedError` |
| **AI Arena v2** | `docs/specs/commandcenter3.md:2767-2907` | `validation_service.py` - ALL methods raise `NotImplementedError` |
| **Intelligence Feed** | `backend/app/routers/intelligence.py:43-49` | Returns `{"items": [], "updated_at": None}` |
| **Attention Queue** | `backend/app/routers/intelligence.py:52-56` | Returns `{"items": []}` |

### 2.2 Hypothesis Service Methods - NotImplementedError

```python
# File: backend/app/services/hypothesis_service.py
generate_hypotheses()  # Line 15-22 - NotImplementedError
get_test_strategy()    # Line 24-33 - NotImplementedError
crystallize()          # Line 35-41 - NotImplementedError
validate_idea()        # Line 43-69 - PARTIAL (basic heuristics only)
```

### 2.3 Validation Service Methods - NotImplementedError

```python
# File: backend/app/services/validation_service.py
validate()      # Line 19-31 - NotImplementedError
ai_arena()      # Line 33-43 - NotImplementedError
web_search()    # Line 45-47 - NotImplementedError
market_data()   # Line 49-51 - NotImplementedError
case_studies()  # Line 53-55 - NotImplementedError
```

### 2.4 Forecasting & Calibration

| Integration | File | Line | Status |
|-------------|------|------|--------|
| Polymarket | `backend/app/services/forecaster_service.py` | 349 | `enabled: False` |
| Metaculus | `backend/app/services/forecaster_service.py` | 353 | `enabled: False` |
| PredictIt | `backend/app/services/forecaster_service.py` | 361 | `enabled: False` |
| Daily Sync Job | NEXT_STEPS.md | 110 | Not implemented |

### 2.5 Frontend Components - NOT BUILT

| Component | Spec Location | Expected File | Status |
|-----------|---------------|---------------|--------|
| Command Palette | `commandcenter3.md:7058` | `CommandPalette.tsx` | Does not exist |
| Hover Portals | `commandcenter3.md:7122` | `HoverPortal.tsx` | Does not exist |
| Timeline Scrubber | `commandcenter3.md:7226` | `TimelineScrubber.tsx` | Does not exist |
| Edge Panels | `commandcenter3.md:7074-7101` | - | Does not exist |
| Live Voice Input | `commandcenter3.md:7133-7163` | - | Does not exist |

### 2.6 Routines System - ZERO IMPLEMENTATION

From `docs/specs/commandcenter3.md:7574-8114` (Section 7.24):

**Checklist items (all unchecked in NEXT_STEPS.md:8352-8370):**
- [ ] Routine data model and database schema
- [ ] Basic CRUD API endpoints
- [ ] Manual trigger execution
- [ ] Simple step types (file, notify)
- [ ] Schedule-based triggers (cron)
- [ ] Calendar and email actions
- [ ] Human pause points with approval UI
- [ ] Workflow recording in Chrome extension
- [ ] VISLZR Routine node type
- [ ] Browser actions (navigate, fill, extract)
- [ ] Agent actions (execute, validate)
- [ ] Visual step editor in VISLZR
- [ ] Inner Council notification integration
- [ ] Advanced scheduling (calendar-aware)

### 2.7 Frontend TODOs

| Feature | File | Line | Status |
|---------|------|------|--------|
| Panel Resizing | `components/panels/PanelContainer.tsx` | 28 | TODO |
| Task Stop Action | `components/Execution/TaskCard.tsx` | 209 | TODO |
| Radial Menu - Wander | `hooks/useRadialMenu.ts` | 52 | Not implemented |
| Radial Menu - Search | `hooks/useRadialMenu.ts` | 56 | Not implemented |
| Radial Menu - Validation | `hooks/useRadialMenu.ts` | 60 | Not implemented |
| Radial Menu - Chat | `hooks/useRadialMenu.ts` | 64 | Not implemented |
| Radial Menu - New Idea | `hooks/useRadialMenu.ts` | 68 | Not implemented |
| WebSocket Real-Time | `hooks/useFlowBoard.ts` | 155 | TODO |
| Backend Persistence | `hooks/useFlowBoard.ts` | 183 | TODO |
| Insight Context Matching | `hooks/useInsights.ts` | 141 | TODO |

### 2.8 Memory & Embeddings

| Feature | File | Lines | Status |
|---------|------|-------|--------|
| Embedding Generation | `backend/app/services/memory_service.py` | 69, 132, 203 | Three TODOs |

### 2.9 Pipeline Hardening (NEXT_STEPS.md:61-63)

- [ ] Phase 1: Fix AsyncAnthropic in extraction service
- [ ] Phase 2: Build complete runtime container
- [ ] Phase 3: Add integration tests and CI validation

### 2.10 Testing & Documentation (NEXT_STEPS.md:121-128)

- [ ] Comprehensive tests for validation, hypothesis, forecaster, observation services
- [ ] API documentation (OpenAPI specs)
- [ ] Performance profiling
- [ ] Security audit
- [ ] Documentation update

---

## Part 3: CC4 Unbuilt Features

### 3.1 Phase Implementation Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 01: Governance Kernel | ✅ LOCKED | Complete |
| Phase 02: State Machines & Permissions | ✅ LOCKED | Jan 30 |
| Phase 03: Decision Primitives | ✅ LOCKED | Jan 30 |
| Phase 04: Evidence & Belief Tracking | ❌ NOT BUILT | Spec exists |
| Phase 05: Memory & Learning | ❌ NOT BUILT | Spec exists |
| Phase 06: Agent Framework | ❌ NOT BUILT | Spec exists |
| Phase 07: Orchestration & Pipelines | ❌ NOT BUILT | Spec exists |
| Phase 08: UI & Interaction Model | ❌ NOT BUILT | Spec exists, UI doesn't match |
| Phase 09: Venture Studio Layer | ❌ NOT STARTED | No docs directory |
| Phase 10: Hardening & Scale | ❌ NOT STARTED | No docs directory |

### 3.2 Validation Service - ALL NotImplementedError

```python
# File: backend/app/services/validation_service.py
validate()      # Line 31 - NotImplementedError
ai_arena()      # Line 43 - NotImplementedError
web_search()    # Line 47 - NotImplementedError
market_data()   # Line 49 - NotImplementedError
case_studies()  # Line 55 - NotImplementedError
```

### 3.3 Hypothesis Service - MOSTLY NotImplementedError

```python
# File: backend/app/services/hypothesis_service.py
generate_hypotheses()  # Line 22 - NotImplementedError
get_test_strategy()    # Line 33 - NotImplementedError
crystallize()          # Line 41 - NotImplementedError
validate_idea()        # Lines 43-69 - PARTIAL (heuristics only)
```

### 3.4 Intelligence Router - ALL TODO

| Endpoint | File | Line | Returns |
|----------|------|------|---------|
| `GET /feed` | `routers/intelligence.py` | 48 | TODO - empty |
| `GET /attention` | `routers/intelligence.py` | 55 | TODO - empty |
| `POST /explore` | `routers/intelligence.py` | 64 | TODO - stub |
| `POST /sources/{source}/sync` | `routers/intelligence.py` | 84 | TODO - stub |

### 3.5 Memory Service - PARTIAL

| Feature | File | Line | Status |
|---------|------|------|--------|
| Vector Search | `services/memory_service.py` | 62 | "TODO: implement vector search" |
| Content Synthesis | `services/memory_service.py` | 181 | "TODO: Use LLM" |
| Contradiction Detection | `services/memory_service.py` | 264 | "TODO: Implement semantic" |

### 3.6 Agent Primitives - NOT INTEGRATED

| Feature | File | Line | Status |
|---------|------|------|--------|
| Memory Service Integration | `agents/primitives/__init__.py` | 147, 169 | "TODO: Integrate" |
| Inter-Agent Communication | `agents/primitives/__init__.py` | 194 | "TODO: Implement" |
| Web Search API | `agents/primitives/__init__.py` | 218 | "TODO: Integrate" |

### 3.7 Phase 08 UI Routes - ALL UNCHECKED

From `docs/central-core/phase-08-ui-interaction-model/checklist.md`:

- [ ] `/explore`
- [ ] `/audit`
- [ ] `/decisions` + `/decisions/:id`
- [ ] `/beliefs` + `/beliefs/:id`
- [ ] `/evidence` + `/evidence/:id`
- [ ] `/agents` + `/agents/:id`
- [ ] `/orchestration` + graph + run routes

### 3.8 UI Governance Issues

From `docs/_archive/issues/UI_ISSUES_AND_INTUITION_CHECK.md`:

- [ ] Two input boxes (unclear which to use)
- [ ] Pipeline management buried in settings
- [ ] No persistent toolbar
- [ ] "Capture" too prominent
- [ ] Brain icon should open modal not page
- [ ] Canvas icon should be eye icon
- [ ] Pipelines not interactive/segmented
- [ ] **Intuition Check Gate** - Not implemented

### 3.9 Frontend TODOs (Mock Data)

| Component | File | Line | Issue |
|-----------|------|------|-------|
| PipelinesPage | `pages/PipelinesPage.tsx` | 52 | Mock data |
| IntelPage | `pages/IntelPage.tsx` | 34 | Mock data |
| IdeasStore | `stores/ideasStore.ts` | 109 | TODO: Get from project |
| IdeasTab | `components/ideas/IdeasTab.tsx` | 29, 73, 97 | Multiple TODOs |
| BrainModal | `components/TopBar/BrainModal.tsx` | 25 | Mock data |
| ProgressBar | `components/TopBar/ProgressBar.tsx` | 11 | TODO: Fetch from API |
| TopBar | `components/TopBar/TopBar.tsx` | 24 | TODO: wire to store |
| DockableChatPanel | `components/DockableChatPanel.tsx` | 68 | TODO: Implement chat |
| PipelineViewer | `components/pipelines/PipelineViewer.tsx` | 97, 161 | TODO: Add types, actions |
| QuickCaptureModal | `components/TopBar/QuickCaptureModal.tsx` | 38, 123 | TODOs |

### 3.10 Ideas Service - NOT INTEGRATED

```python
# File: backend/app/services/ideas_service.py
# Line 100: TODO: Integrate with validation service
# Line 120: TODO: Integrate with plan generation service
# Line 140: TODO: Integrate with autonomous execution service
```

### 3.11 UX Validation Service - PARTIAL

```python
# File: backend/app/services/ux_validation_service.py
# Line 337: TODO (Phase 3): Implement anti-pattern detection
# Line 360: TODO (Phase 4): Implement challenge workflow logic
```

### 3.12 Forecaster Service - DISABLED

```python
# File: backend/app/services/forecaster_service.py
# Lines 349-363: All integrations have enabled: False
```

### 3.13 Archived Skills (Previously Planned)

| Skill | Status |
|-------|--------|
| `frontend-composability` | Archived |
| `agent-native-architecture` | Archived |
| `visual-memory` | Archived |
| `agent-sandboxes` | Archived |
| `long-running-agents` | Archived |
| `dagger-execution` | Archived |

---

## Part 4: Cross-Project Feature Gaps

### 4.1 Features in V1 Not in Later Versions

| Feature | V1 Status | V2 Status | CC4 Status |
|---------|-----------|-----------|------------|
| Hub Spawning | ✅ Built | ❌ Lost | ❌ Lost |
| NATS Federation | ✅ Built | ⚠️ Optional | ❌ None |
| Celery Task Queue | ✅ Built | ❌ Removed | ❌ None |
| Redis Caching | ✅ Built | ❌ Removed | ❌ None |
| Flower Monitoring | ✅ Built | ❌ Removed | ❌ None |
| PostgreSQL + pgvector | ✅ Primary | ⚠️ Optional | ⚠️ Ready |
| 1,700+ Tests | ✅ | ~100 | ~50 |

### 4.2 Features Planned Across All Versions But Never Built

| Feature | First Planned | Current Status |
|---------|---------------|----------------|
| Wander Agent | V1 | Not implemented in any version |
| Voice Input | V1 | Not implemented in any version |
| Global Reputation Monitoring | V1 | Detailed spec, never built |
| Polymarket Integration | V1 | Disabled in V2/CC4 |
| Hypothesis Generation (LLM) | V1 | NotImplementedError in V2/CC4 |
| AI Arena Multi-Model | V1 | NotImplementedError in V2/CC4 |
| Command Palette | V2 | Not built |
| Routines System | V2 | Zero implementation |
| Timeline Scrubber | V2 | Not built |

### 4.3 Recurring TODOs Across Codebases

| Pattern | V1 Count | V2 Count | CC4 Count |
|---------|----------|----------|-----------|
| `# TODO:` | 24+ | 60+ | 50+ |
| `NotImplementedError` | 3 | 8 | 10 |
| `enabled: False` | 2 | 3 | 3 |
| Mock data / hardcoded | 5 | 10 | 15 |

---

## Part 5: Priority Recommendations

### P0 - Critical (Blocks Core Value)

1. **Validation Service** - All versions have NotImplementedError
2. **Hypothesis Engine** - Core to CC value proposition
3. **Wander Agent** - Autonomous exploration (key differentiator)
4. **Hub Spawning** - Multi-project isolation (lost from V1)
5. **Memory/Embedding Service** - Vector search needed

### P1 - High (Major Features)

6. **AI Arena v2** - Multi-model consensus
7. **Intelligence Feed** - Aggregated insights
8. **Source Curator** - HN/arXiv/SEC integration
9. **Routines System** - Workflow automation
10. **Command Palette** - Natural language navigation

### P2 - Medium (Enhancement)

11. **Forecaster Integrations** - Polymarket, Metaculus
12. **Real-time WebSocket** - Collaborative updates
13. **Timeline Scrubber** - Temporal navigation
14. **Voice Input** - Multi-modal capture
15. **Cross-project Insights** - Pattern detection

### P3 - Low (Polish)

16. **API Documentation** - OpenAPI specs
17. **Test Coverage** - Comprehensive tests
18. **Performance Profiling**
19. **Security Audit**
20. **UI Polish** - Match spec exactly

---

## Appendix: File Locations Quick Reference

### CommandCenter V1
```
/Users/danielconnolly/Projects/CC4/CommandCenter/
├── backend/app/tasks/           # Celery task stubs
├── backend/app/routers/         # API endpoints with TODOs
├── backend/app/services/        # Service implementations
├── docs/plans/                  # Phase plans & specs
├── docs/ROADMAP.md              # Feature roadmap
└── hub/                         # Hub orchestration (BUILT)
```

### CommandCenter 2.0
```
/Users/danielconnolly/Projects/CC4/CommandCenter2.0/
├── backend/app/services/        # NotImplementedError methods
├── backend/app/routers/         # API stubs
├── docs/specs/commandcenter3.md # 7,896 line master spec
├── NEXT_STEPS.md                # Unchecked items
└── skills/                      # 25+ skill definitions
```

### CC4
```
/Users/danielconnolly/Projects/CC4/
├── backend/app/services/        # NotImplementedError methods
├── backend/app/agents/          # Agent primitives with TODOs
├── docs/central-core/phase-*/   # Phase specs (04-10 not built)
├── docs/_archive/               # Abandoned features
├── frontend/src/                # Mock data throughout
└── skills/archive/              # Archived skills
```

---

*Generated: 2026-01-31*
*Source: Parallel agent exploration of CommandCenter, CommandCenter2.0, and CC4 codebases*
