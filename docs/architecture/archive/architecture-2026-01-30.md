# CommandCentral Architecture Planning Document

> **Date:** 2026-01-30
> **Status:** Draft - Open Questions Pending
> **Scope:** Split CC4 into 4 distinct services with unified orchestration

---

## Executive Summary

CC4 (CommandCenter 4.0) is being split into **4 distinct services**, each with its own backend, frontend, and KnowledgeBeast instance:

| Service | Purpose | Core Responsibility |
|---------|---------|---------------------|
| **CommandCentral** | Governance & Truth State | State machines, permissions, audit, decisions |
| **PIPELZR** | Codebase Indexing & Execution | Code analysis, task execution, pipelines |
| **VISLZR** | Visualization & Exploration | Canvas, graphs, wander navigation |
| **IDEALZR** | Ideas & Strategic Intelligence | Goals, hypotheses, evidence, forecasting |

---

## Part 1: Historical Architecture Analysis

### 1.1 CommandCenter (Original)

**Tech Stack:**
- FastAPI + SQLAlchemy (async)
- PostgreSQL 16 + pgvector
- Redis (caching)
- **NATS JetStream** (event streaming)
- Prometheus + Grafana (monitoring)

**Key Patterns:**
- Event-driven architecture via NATS
- Subject namespace: `graph.indexed.{project_id}`, `audit.requested.{kind}`
- Correlation ID tracking across all requests
- Multi-tenant isolation via Projects
- Graceful degradation (NATS optional)

**Services:** 55+ services including RAGService, GitHubService, GraphService, KnowledgeBeast

**Strengths:**
- Mature service layer pattern
- Excellent observability (correlation tracking, metrics)
- Event-driven decoupling
- Async-first design

**Weaknesses:**
- Infrastructure complexity (NATS + Redis + PostgreSQL)
- Potentially over-engineered for actual use patterns

---

### 1.2 CommandCenter 2.0

**Tech Stack:**
- FastAPI + SQLAlchemy
- SQLite (dev) / PostgreSQL (prod)
- **No NATS** - Direct REST + WebSocket/SSE
- Dagger SDK for container orchestration

**Key Patterns:**
- Direct REST calls between services (synchronous)
- Database as event log
- WebSocket for real-time streaming
- Three execution modes: Local (FREE), Dagger (isolated), E2B (cloud)

**Services:** 31 services focused on agent execution, long-running orchestration

**Strengths:**
- Simpler infrastructure (no message bus)
- Excellent Dagger integration for parallel execution
- OAuth support for free Claude Max usage
- Robust session recovery

**Weaknesses:**
- Tight coupling via direct REST calls
- Less suited for true microservice distribution

**Key Insight:** CC2.0 moved **away** from NATS, suggesting the complexity wasn't justified for the use case.

---

## Part 2: CC4 Current State (Comprehensive Inventory)

### 2.1 Backend Components

#### API Routers (47 total, 140+ endpoints)

**Core:**
| Router | Path | Purpose |
|--------|------|---------|
| auth | `/api/v1/auth` | User authentication |
| chat | `/api/v1/chat` | Chat + streaming |
| tasks | `/api/v1/tasks` | Task CRUD |
| projects | `/api/v1/projects` | Project management |
| memory | `/api/v1/memory` | Provenance-first claims |
| personas | `/api/v1/personas` | Persona management |
| skills | `/api/v1/skills` | Skill registry |

**Strategic:**
| Router | Path | Purpose |
|--------|------|---------|
| goals | `/api/v1/strategic/goals` | Goal hierarchy |
| hypotheses | `/api/v1/strategic/hypotheses` | Hypothesis tracking |
| evidence | `/api/v1/strategic/evidence` | Evidence collection |
| decisions | `/api/v1/decisions` | Decision primitives |
| ventures | `/api/v1/ventures` | Venture studio |

**Execution:**
| Router | Path | Purpose |
|--------|------|---------|
| autonomous | `/api/v1/autonomous` | Long-running execution |
| agents | `/api/v1/agents` | Agent sessions |
| pipeline | `/api/v1/pipeline` | Batch orchestration |
| state-machine | `/api/v1/state-machine` | State + permissions |

**Intelligence:**
| Router | Path | Purpose |
|--------|------|---------|
| intelligence | `/api/v1/intelligence` | Signal extraction |
| knowledge | `/api/v1/knowledge` | KnowledgeBeast |
| search | `/api/v1/search` | Unified search |
| forecaster | `/api/v1/forecaster` | Predictions |

**UX Validation:**
| Router | Path | Purpose |
|--------|------|---------|
| ux | `/api/v1/ux` | Validation gates |
| ux-audit | `/api/v1/ux-audit` | Audit pipeline |
| ux-pipeline | `/api/v1/ux-pipeline` | UX execution |

**Other:** arena, revenue, scanners, feedback, retrospective, tutorial, me, context, browser, extension, events, llm, skill-governance, demo, commands

#### Services (71 total)

**Chat & Communication:**
- ChatService, DaggerChatService, ChatKnowledgeCapture, ChatContextManager, ChatIntentDetector

**Memory & Knowledge:**
- MemoryService, KnowledgeService, UnifiedSearchService, ObservationService, SignalExtractor

**Strategic:**
- GoalsService, HypothesesService, EvidenceService, RevenueService, ForecastingService

**Execution:**
- ExecutionRunner, ExecutionWorker, ParallelExecutionRunner (92-97% efficiency)
- ParallelOrchestrator, BatchOrchestrator, LongRunningOrchestrator, TaskExecutor

**Agent:**
- AgentService, AutonomousTaskWorker, ArenaService, ArenaJudge
- InnerCouncil: Strategist, Conflict, Synthesizer, Validation

**UX Validation:**
- UXValidationService, ComponentClassifier, ChallengeWorkflowManager
- 8 Gates: Composability, FeatureHierarchy, InformationArchitecture, IntuitionCheck, Personalization, ProgressiveDisclosure, RoleVisibility
- 8 Detectors: CognitiveOverload, ColorSemanticConfusion, FeatureHierarchyViolation, GenericLabels, MissingLoadingStates, NestedModals, RoleVisibilityViolation, ScatteredRelatedData

**Skills:**
- SkillsService, SkillGovernance, SkillSyncService

**Other:** ProjectService, ContextService, LearningService, FeedbackService, DemoService, TutorialService, LLMProvider, AuthService, PersonaService, and more

#### Database Models (35 total)

**Core:** User, Project, Task, ActiveDocument
**Strategic:** Goal, Hypothesis, Evidence
**Execution:** ChatMessage, Agent, ParallelTestSession
**Validation:** UXAudit, UXClassification, ChallengeWorkflow, ValidationHistory
**Analytics:** UserFeedback, SessionRetrospective, AuditEntry, PipelineConfig
**Supporting:** Idea, Persona, Skill, Arena, Decision, Venture, DemoSession, TutorialScenario, Scanner, Revenue

#### Infrastructure

**Middleware:** CORS, RequestLogging, RequestSizeLimit, RateLimit, Metrics
**Database:** SQLite WAL mode (async), SQLAlchemy
**Auth:** JWT HS256 (24hr expiration)
**Monitoring:** Prometheus metrics at `/metrics`

---

### 2.2 Frontend Components

#### Pages (9)
- ChallengeWorkflowDemo, ContextPage, ExplorePage, IntelPage
- PipelinesPage, SettingsPage, StrategicPage, VenturesPage, WelcomePage

#### Major Component Groups (150+ components)

**Canvas/Visualization:**
- Canvas, EvidenceCoverageBar, HypothesisDetailPanel, NodeChatPanel, NodeToolbar
- Nodes: ConfidenceRing, EvidenceNode, GoalNode, HypothesisNode, IdeaNode, InsightNode, TaskNode

**Strategic Intelligence:**
- GoalForm, GoalsList, HypothesisForm, HypothesesList, HypothesisKanban
- EvidenceCard, EvidenceForm, EvidenceList, ConfidenceSlider
- ForecasterModal, PredictionCard

**Execution/Tasks:**
- Kanban, TaskCard, ExecutionView, AgentProgress, AgentStream
- TaskDetailDrawer with tabs (Overview, Subtasks, Logs)
- Modals: CreateTask, EditTask, DeleteConfirm, AITaskReview, AddAgent

**Pipelines:**
- PipelineViewer (unified), PipelineCard (any type)

**Ventures:**
- IntakeWizard: DetailsStep, RegimeStep, ChallengeStep, KillConditionsStep, ReviewStep

**VISLZR:**
- WanderCanvas, VislzrNode, Breadcrumb, QueryInput, SiblingPanel

**Other:** Chat, Dashboard, Context, IntelligenceFeed, Search, Arena, Settings, Tutorial, Help, Feedback, Onboarding

#### Zustand Stores (23)
- activityStore, aiAssistantStore, canvasStore, challengeStore, chatStore
- contextStore, executionStore, feedbackStore, focusStore, helpStore
- ideasStore, intelligenceStore, layoutStore, onboardingStore, personasStore
- projectsStore, queryStore, searchStore, taskProgressStore, toastStore
- tutorialStore, venturesStore, vislzrStore

#### API Client Functions (100+)
- projectsApi, tasksApi, personasApi, agentsApi, chatApi
- pipelineApi, goalsApi, hypothesesApi, evidenceApi, knowledgeApi
- contextApi, searchApi, predictionsApi, venturesApi, uxAuditApi
- skillsApi, autonomousApi

#### Hooks (12)
- useArena, useAutonomousWebSocket, useEventBroadcaster, useExecutionModals
- useInsights, useModal, useProjectFocus, useRecentActivity
- useRevenue, useSkillInjection, useStrategicAPI, useVentures

---

## Part 3: Proposed 4-Service Architecture

### 3.1 Service Definitions

#### CommandCentral (Governance & Truth)
**Responsibility:** Single source of truth for system state, permissions, and audit

**Owns:**
- State machine engine (entity states, transitions)
- Permission matrix (role-based authorization)
- Audit log (all state changes, allow/deny events)
- Decision primitives (draft → active → decided → archived)
- User authentication
- Cross-service coordination

**From CC4:**
- Routers: auth, state-machine, decisions, events
- Services: StateMachineService, AuditService, AuthService
- Models: User, AuditEntry, Decision

**KnowledgeBeast Instance:** Governance rules, audit history, permission policies

---

#### PIPELZR (Codebase & Execution)
**Responsibility:** Code indexing, task execution, pipeline orchestration

**Owns:**
- Codebase indexing and analysis
- Task execution (local, Dagger, E2B)
- Pipeline orchestration (batch, parallel)
- Worktree pool management
- Agent session management
- Skill execution

**From CC4:**
- Routers: tasks, agents, autonomous, pipeline, skills, skill-governance
- Services: ExecutionRunner, ParallelExecutionRunner, AgentService, LongRunningOrchestrator, SkillsService, WorktreePool
- Models: Task, Agent, ParallelTestSession, Skill

**KnowledgeBeast Instance:** Code documentation, indexed symbols, execution history

---

#### VISLZR (Visualization & Exploration)
**Responsibility:** Visual exploration, canvas navigation, graph rendering

**Owns:**
- Canvas/graph visualization
- Wander navigation
- Node rendering (all entity types)
- Exploration queries
- Relationship visualization

**From CC4:**
- Frontend: Canvas/, Vislzr/, nodes/, WanderCanvas
- Stores: canvasStore, vislzrStore
- Components: All node types, breadcrumb, sibling panel

**KnowledgeBeast Instance:** Graph relationships, exploration paths, visual layouts

---

#### IDEALZR (Ideas & Strategic Intelligence)
**Responsibility:** Strategic planning, hypothesis tracking, evidence management

**Owns:**
- Goals hierarchy and progress
- Hypotheses lifecycle
- Evidence collection and linking
- Predictions and forecasting
- Venture studio
- Ideas capture
- Intelligence feed
- Memory/claims (provenance-tracked)

**From CC4:**
- Routers: strategic/*, ventures, forecaster, intelligence, memory, ideas
- Services: GoalsService, HypothesesService, EvidenceService, ForecastingService, VenturesService, MemoryService, IntelligenceService
- Models: Goal, Hypothesis, Evidence, Venture, Prediction, Idea

**KnowledgeBeast Instance:** Strategic knowledge, evidence corpus, forecasting data

---

### 3.2 Service Boundary Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CommandCentral                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   IDEALZR       │    │   VISLZR        │    │   PIPELZR       │         │
│  │                 │    │                 │    │                 │         │
│  │  Goals          │    │  Canvas         │    │  Tasks          │         │
│  │  Hypotheses     │◄──►│  Wander         │◄──►│  Agents         │         │
│  │  Evidence       │    │  Graphs         │    │  Pipelines      │         │
│  │  Ventures       │    │  Nodes          │    │  Execution      │         │
│  │  Forecasting    │    │                 │    │  Skills         │         │
│  │  Memory         │    │                 │    │  Code Index     │         │
│  │                 │    │                 │    │                 │         │
│  │  [KB Instance]  │    │  [KB Instance]  │    │  [KB Instance]  │         │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  │                                          │
│                                  ▼                                          │
│                    ┌─────────────────────────┐                              │
│                    │    CommandCentral       │                              │
│                    │                         │                              │
│                    │  State Machine          │                              │
│                    │  Permissions            │                              │
│                    │  Audit Log              │                              │
│                    │  Decisions              │                              │
│                    │  Auth                   │                              │
│                    │                         │                              │
│                    │  [KB Instance]          │                              │
│                    └─────────────────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 4: Inter-Service Communication Options

### Option A: REST API (Direct Calls)

```
Service A ──HTTP──► Service B
            └──────► Response
```

**Pros:**
- Simple, well-understood
- Easy debugging (HTTP traces)
- No additional infrastructure

**Cons:**
- Tight coupling
- Sync blocking (cascading failures)
- Hard to add consumers

**Best for:** Queries ("Get decision X", "List tasks")

---

### Option B: NATS JetStream (Event-Driven)

```
Service A ──publish──► NATS ──subscribe──► Service B
                           ──subscribe──► Service C
                           ──subscribe──► Service D
```

**Pros:**
- Loose coupling
- Multiple consumers per event
- Event replay/persistence
- Natural for audit trails

**Cons:**
- Infrastructure complexity
- Harder debugging
- Learning curve

**Best for:** Events ("Decision approved", "Evidence added", "Task completed")

---

### Option C: Hybrid (Recommended)

```
Queries:    Service A ──REST──► Service B
Events:     Service A ──NATS──► [All interested services]
Gateway:    Frontend ──REST──► API Gateway ──routes──► Services
```

**Pattern:**
- REST for synchronous queries
- NATS for async events (state changes, audit events)
- API Gateway for frontend (single entry point)

---

## Part 5: Open Questions

### Architecture Questions

1. **Communication Pattern:** Which option - REST only, NATS only, or Hybrid?
   - CC2.0 moved away from NATS. Was that the right call?
   - Do we need event replay/persistence?

2. **API Gateway:** Should there be a unified gateway, or does each service expose its own API to the frontend?

3. **Shared Database vs Separate:**
   - Should CommandCentral own a shared database for cross-service queries?
   - Or full separation with API calls for cross-service data?

4. **KnowledgeBeast Isolation:** Each service gets its own instance, but:
   - How do cross-service searches work?
   - Is there a federated search capability needed?

5. **Authentication Flow:**
   - CommandCentral owns auth, but how do other services validate tokens?
   - JWT with shared secret? Token introspection endpoint?

### Domain Questions

6. **Project Scope:** Projects span all services. Who owns the Project entity?
   - CommandCentral (governance)?
   - Or each service has a local projection?

7. **UX Validation:** Where does it live?
   - PIPELZR (it validates code/UI)?
   - CommandCentral (it's a governance gate)?
   - Separate service?

8. **Chat:** Where does chat live?
   - IDEALZR (it's about ideas/strategy)?
   - PIPELZR (it drives execution)?
   - All services have chat capability?

9. **Real-time Updates:** How do UI updates propagate?
   - WebSocket per service?
   - Central WebSocket hub?
   - NATS → WebSocket bridge?

10. **Shared Components:** What about UI components used across services?
    - Shared component library?
    - Each service duplicates?
    - Micro-frontends?

### Migration Questions

11. **Migration Order:** Which service to extract first?
    - CommandCentral (foundation)?
    - PIPELZR (most independent)?
    - IDEALZR (cleanest domain boundary)?

12. **Transition Period:** How long do we run both architectures?
    - Big bang cutover?
    - Gradual migration with feature flags?

13. **Data Migration:** How to split the current CC4 database?
    - Export/import?
    - Live sync during transition?

---

## Part 6: Recommendations

### 6.1 Communication: Start Simple, Add Complexity as Needed

**Phase 1:** REST-only between services
- Simpler to build, debug, and operate
- CC2.0 proved this works

**Phase 2:** Add NATS for specific event streams
- Audit events (CommandCentral → all)
- State change notifications
- Only when REST polling becomes a bottleneck

### 6.2 Service Extraction Order

1. **CommandCentral first** - It's the foundation (auth, state, audit)
2. **PIPELZR second** - Clear boundary (execution is isolated)
3. **IDEALZR third** - Depends on CommandCentral for governance
4. **VISLZR last** - Primarily frontend, depends on all others for data

### 6.3 Shared Infrastructure

- **PostgreSQL** per service (not shared)
- **KnowledgeBeast** per service (federated search API if needed)
- **Redis** optional per service (caching)
- **NATS** shared cluster (if/when added)

### 6.4 Frontend Strategy

- **Micro-frontend** approach: Each service owns its UI slice
- **Shared component library** for common elements (buttons, cards, etc.)
- **Shell application** in CommandCentral that composes the micro-frontends

---

## Part 7: Next Steps

1. **Decide communication pattern** (REST vs Hybrid)
2. **Define API contracts** between services
3. **Create CommandCentral service** (extract from CC4)
4. **Set up CommandCentral monorepo structure**
5. **Establish CI/CD for multi-service deployment**

---

## Appendix: Component Mapping

### What Goes Where

| Current CC4 Component | Target Service |
|-----------------------|----------------|
| auth router | CommandCentral |
| state-machine router | CommandCentral |
| decisions router | CommandCentral |
| events router | CommandCentral |
| tasks router | PIPELZR |
| agents router | PIPELZR |
| autonomous router | PIPELZR |
| pipeline router | PIPELZR |
| skills router | PIPELZR |
| strategic/* routers | IDEALZR |
| ventures router | IDEALZR |
| forecaster router | IDEALZR |
| intelligence router | IDEALZR |
| memory router | IDEALZR |
| ideas router | IDEALZR |
| Canvas components | VISLZR |
| Vislzr components | VISLZR |
| Node components | VISLZR |
| chat router | TBD (all services?) |
| ux/* routers | TBD (PIPELZR or CommandCentral?) |
| projects router | TBD (CommandCentral?) |
| knowledge router | All (per-service KB) |

---

*Document generated: 2026-01-30*
*Status: Awaiting decisions on open questions*
