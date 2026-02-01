# Project Federation: Multi-Project Architecture

> **Date:** 2026-02-01
> **Status:** Design Draft
> **Source:** Session conversation
> **Priority:** Future Phase

---

## Overview

CommandCentral serves as a **hub** for multiple projects that use its core infrastructure. Each project (Wildvine, future projects) maintains its own KB but can receive improvements from CommandCentral and contribute discoveries back.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      COMMANDCENTRAL (Hub)                                │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  Core Services                                                  │     │
│  │  - KnowledgeBeast (CC's own KB)                                │     │
│  │  - Arena, Skills, Pipelines, Hooks                             │     │
│  │  - Tech Radar (self-improvement pipeline)                      │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  Project Registry                                               │     │
│  │  - View all connected projects                                  │     │
│  │  - Initialize new projects                                      │     │
│  │  - Push improvements (firmware-style)                           │     │
│  │  - Receive discoveries from projects                            │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                    │                                     │
│              ┌─────────────────────┼─────────────────────┐              │
│              │                     │                     │              │
│              ▼                     ▼                     ▼              │
│       ┌───────────┐         ┌───────────┐         ┌───────────┐        │
│       │ Wildvine  │◄───────►│ Project B │◄───────►│ Project C │        │
│       │ (own KB)  │         │ (own KB)  │         │ (own KB)  │        │
│       └───────────┘         └───────────┘         └───────────┘        │
│              │                     │                     │              │
│              └─────────────────────┴─────────────────────┘              │
│                          Bidirectional                                   │
│                     Improvement Sharing                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Two Operating Modes

### 1. Project Initialization (One-time Setup)

When onboarding a new project:

```
CommandCentral                          New Project
     │                                       │
     │  1. Scan project repo                 │
     │─────────────────────────────────────►│
     │                                       │
     │  2. Analyze structure, patterns       │
     │◄─────────────────────────────────────│
     │                                       │
     │  3. Configure:                        │
     │     - Governance (allowed/blocked)    │
     │     - Constitution (principles)       │
     │     - Skills to share                 │
     │     - Knowledge to sync               │
     │─────────────────────────────────────►│
     │                                       │
     │  4. Project has own KB               │
     │     (explicit sync, not federated)    │
     │                                       │
```

**What gets configured:**
- Governance rules (what's allowed/blocked for this project)
- Constitution (principles, intent enforcement settings)
- Which skills from CC to copy to project
- Which knowledge collections to sync initially
- Each project maintains its own independent KB

### 2. Ongoing Improvement Sharing (Bidirectional)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TECH RADAR PIPELINE                                   │
│                                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌───────┐ │
│  │  SCAN    │──►│ EVALUATE │──►│   PLAN   │──►│  TEST    │──►│NOTIFY │ │
│  │ (Cron)   │   │ (Score)  │   │(If pass) │   │(Sandbox) │   │(Human)│ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └───────┘ │
│       │                                             │             │     │
│       │                                             │             ▼     │
│  Papers, posts,                              Security:     One-click    │
│  resources about                             - Prompt injection        │
│  AI agents                                   - All OWASP               │
│                                              - Sanitization            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Radar: Self-Improvement Pipeline

### Purpose

Continuous scanning for improvements relevant to AI agent usage, with automated evaluation and human-gated approval.

### Pipeline Stages

| Stage | Description | Trigger |
|-------|-------------|---------|
| **Scan** | Cron job scans papers, blogs, tools (e.g., agent-trace.dev) | Scheduled |
| **Evaluate** | Review relevance, score against threshold | Automatic |
| **Plan** | If "worthwhile", create implementation plan | If score passes |
| **Test** | Sandbox testing with security validation | Automatic |
| **Notify** | Human review with full context | Automatic |
| **Approve** | One-click approval to deploy | Human action |

### Security Testing (Mandatory)

Before any improvement is approved:
- Prompt injection testing
- OWASP Top 10 validation
- Input sanitization verification
- Sandbox isolation confirmation
- Rollback strategy defined

### Scoring Threshold

```python
class ImprovementScore:
    relevance: float      # 0-1: How relevant to our use case
    impact: float         # 0-1: Potential impact on agent quality
    risk: float           # 0-1: Security/stability risk
    effort: float         # 0-1: Implementation effort

    @property
    def worthwhile(self) -> bool:
        # High relevance + high impact + low risk + reasonable effort
        return (
            self.relevance > 0.7 and
            self.impact > 0.5 and
            self.risk < 0.3 and
            self.effort < 0.7
        )
```

---

## Bidirectional Communication

### CommandCentral → Projects (Push)

"Firmware upgrade" style:

```python
@dataclass
class ImprovementPackage:
    """Improvement ready for distribution to projects."""

    id: str
    type: Literal["skill", "knowledge", "config", "security_patch"]

    # What's included
    content: Any
    version: str

    # Why it matters
    description: str
    source_url: Optional[str]  # e.g., "https://agent-trace.dev/"

    # Approval
    tested_at: datetime
    security_validated: bool
    approved_by: str

    # Distribution
    applicable_to: list[str]  # Project IDs or ["all"]
    priority: Literal["critical", "recommended", "optional"]

async def distribute_improvement(package: ImprovementPackage):
    """Push improvement to applicable projects."""

    for project_id in package.applicable_to:
        project = await registry.get_project(project_id)

        # Create notification for project
        await project.notify(
            type="improvement_available",
            package=package,
            action_url=f"/improvements/{package.id}/apply"
        )
```

### Projects → CommandCentral (Report)

When a project discovers something useful:

```python
@dataclass
class ProjectDiscovery:
    """Discovery from a project that might benefit others."""

    project_id: str
    discovered_at: datetime

    # What was found
    type: Literal["tool", "paper", "technique", "pattern"]
    title: str
    description: str
    source_url: Optional[str]

    # Project's assessment
    relevance_score: float
    tested_locally: bool
    local_results: Optional[str]

    # Recommendation
    recommend_for: list[str]  # ["commandcentral", "all", "similar_projects"]

async def report_discovery(discovery: ProjectDiscovery):
    """Project reports discovery to CommandCentral."""

    # Add to CC's Tech Radar queue for evaluation
    await tech_radar.add_to_queue(
        source="project_report",
        project_id=discovery.project_id,
        content=discovery
    )

    # Notify CC maintainers
    await notify_maintainers(
        f"Project {discovery.project_id} reported: {discovery.title}"
    )
```

---

## UI Requirements

### CommandCentral Dashboard

| Feature | Description |
|---------|-------------|
| **Project List** | View all connected projects |
| **Project Status** | Health, last sync, pending improvements |
| **Initialize Project** | Scan repo, configure governance/constitution |
| **Improvement Queue** | Pending improvements from Tech Radar |
| **Discovery Feed** | Reports from projects |

### Actions Available (View + Initialize)

1. **View projects** - Status, health, configuration
2. **Initialize new project** - Scan, configure, set up governance
3. **View pending improvements** - What's in the Tech Radar queue
4. **View project discoveries** - What projects have reported

*Note: Full management and orchestration deferred to later phase*

---

## Data Model

```python
@dataclass
class RegisteredProject:
    """A project connected to CommandCentral."""

    id: str
    name: str
    repo_path: str

    # Configuration
    governance: GovernanceConfig
    constitution: ConstitutionConfig
    shared_skills: list[str]      # Skill IDs synced from CC
    shared_knowledge: list[str]   # KB collection IDs synced from CC

    # Communication
    kb_endpoint: Optional[str]    # Project's KB API (if exposed)
    webhook_url: Optional[str]    # For push notifications

    # Status
    last_sync: datetime
    last_discovery_report: Optional[datetime]
    pending_improvements: list[str]  # Package IDs not yet applied

@dataclass
class GovernanceConfig:
    """What's allowed/blocked for a project."""

    allowed_tools: list[str]
    blocked_tools: list[str]
    allowed_providers: list[str]
    max_autonomy_level: int  # 1-5
    require_human_approval: list[str]  # Action types

@dataclass
class ConstitutionConfig:
    """Principles and rules for a project."""

    failure_policy: FailurePolicy  # Default: FAIL_LOUD
    preflight_required: bool       # Default: True
    intent_enforcement: bool       # Default: True
    knowledge_capture: bool        # Default: True
    custom_principles: list[str]   # Project-specific
```

---

## Implementation Phases

### Phase 1: Project Registry (Near-term)
- [ ] Basic project registration
- [ ] View projects in UI
- [ ] Manual project initialization

### Phase 2: Tech Radar Pipeline (Future)
- [ ] Cron-based scanning
- [ ] Evaluation and scoring
- [ ] Sandbox testing
- [ ] Security validation
- [ ] Human notification + one-click approval

### Phase 3: Bidirectional Communication (Future)
- [ ] Push improvements to projects
- [ ] Receive discoveries from projects
- [ ] Cross-project relevance matching

---

## Open Questions

1. **Transport mechanism**: Webhooks? MCP? Direct API calls?
2. **Versioning**: How to handle version conflicts when projects diverge?
3. **Security**: How to authenticate project ↔ CC communication?
4. **Rollback**: If an improvement causes issues in a project, how to revert?
5. **Discovery routing**: How to determine which projects a discovery is relevant to?

---

## Example: agent-trace.dev Discovery

```
Tech Radar scans → Finds agent-trace.dev
                          │
                          ▼
              ┌─────────────────────┐
              │ EVALUATE            │
              │ - Relevance: 0.9    │ (directly about agent observability)
              │ - Impact: 0.8       │ (could improve debugging)
              │ - Risk: 0.2         │ (well-documented, OSS)
              │ - Effort: 0.4       │ (integration work needed)
              │ → Score: WORTHWHILE │
              └─────────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │ PLAN                │
              │ - Add to observ.    │
              │ - Trace agent calls │
              │ - Dashboard widget  │
              └─────────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │ TEST (Sandbox)      │
              │ - Security: PASS    │
              │ - Integration: PASS │
              │ - Performance: OK   │
              └─────────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │ NOTIFY              │
              │ "agent-trace.dev    │
              │  integration ready" │
              │ [APPROVE] [REJECT]  │
              └─────────────────────┘
                          │
                    Human clicks
                      APPROVE
                          │
                          ▼
              ┌─────────────────────┐
              │ DISTRIBUTE          │
              │ - Push to Wildvine  │
              │ - Push to Project B │
              │ (as firmware update)│
              └─────────────────────┘
```

---

*"Projects should benefit from each other's discoveries without manual coordination."*
