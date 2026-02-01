# Pipeline Architecture: Universal Design

> **Date:** 2026-01-31
> **Status:** Design Draft
> **Source:** Wildvine session conversation
> **Scope:** Unified pipeline model for CC4, CommandCentral, Wildvine, The Vine, all services

---

## Core Principle: Everything Is a Pipeline

A pipeline is: **Input → Stages → Output, with configurable behavior at each stage**

This applies to:
- AI Arena (multi-agent debate)
- UX/UI Validation
- Knowledge Radar (ingestion)
- Idea → Hypothesis → Execute
- The Vine (agent ideation)
- Principle Garden (Wildvine)
- Any multi-step process

---

## The Problems

### 1. Pipelines Are Everywhere But Disconnected

| Pipeline | Location | Self-Configuring? | Visualizable? |
|----------|----------|-------------------|---------------|
| UX/UI Validation | CC4 | Partial | No |
| AI Arena | CC4 | No | No |
| Knowledge Radar | Wildvine | No | No |
| Idea → Hypothesis → Execute | IDEALZR | No | No |
| The Vine (agent discussions) | Future | No | No |
| Principle Garden | Wildvine | No | No |

### 2. No Pipeline Visualization

Can't see:
- What pipelines exist
- What state they're in
- How to modify them
- How they connect to each other

### 3. No Unified Model

Each pipeline is implemented differently, making it hard to:
- Add new stages
- Share components
- Apply consistent failure handling
- Track provenance

---

## Universal Pipeline Model

### Core Data Structures

```python
@dataclass
class Pipeline:
    id: str
    name: str
    domain: str                    # "cc4", "commandcentral", "wildvine", etc.
    stages: list[Stage]
    config: PipelineConfig
    state: PipelineState

    # Self-configuration
    knowledge_sources: list[str]   # KB collections to watch
    skill_sources: list[str]       # Skill registries to watch

@dataclass
class Stage:
    id: str
    name: str
    executor: Executor             # What runs this stage
    inputs: list[Input]            # What it needs
    outputs: list[Output]          # What it produces
    on_failure: FailurePolicy      # What to do if it fails
    required: bool                 # Can pipeline continue without this?
    position: int                  # Order in pipeline

@dataclass
class PipelineConfig:
    # User's explicit intent
    required_participants: list[str]   # These MUST participate
    optional_participants: list[str]   # Nice to have

    # Failure handling
    on_required_missing: FailurePolicy = FailurePolicy.FAIL_LOUD
    on_optional_missing: FailurePolicy = FailurePolicy.ESCALATE

    # Verification
    pre_flight_check: bool = True
    require_pre_flight_pass: bool = True

    # Self-configuration
    self_configuring: bool = False
```

### Failure Policies

```python
class FailurePolicy(Enum):
    # NEVER use these (the bad defaults)
    SILENT_SKIP = "silent_skip"       # Skip and don't tell anyone
    SILENT_SUBSTITUTE = "silent_sub"  # Use alternative without asking

    # ALWAYS use these (the good policies)
    FAIL_LOUD = "fail_loud"           # Stop and report
    ASK_USER = "ask_user"             # Ask what to do
    RETRY_WITH_BACKOFF = "retry"      # Try again with delay
    ESCALATE = "escalate"             # Notify and continue if allowed

# Default must be FAIL_LOUD or ASK_USER, never silent
DEFAULT_FAILURE_POLICY = FailurePolicy.FAIL_LOUD
```

---

## Pipeline Registry

All pipelines register themselves centrally:

```python
class PipelineRegistry:
    """Central registry of all pipelines across all services."""

    pipelines: dict[str, Pipeline]

    def register(self, pipeline: Pipeline):
        self.pipelines[pipeline.id] = pipeline
        self.emit_event("pipeline.registered", pipeline)

    def get_all(self) -> list[Pipeline]:
        return list(self.pipelines.values())

    def get_by_domain(self, domain: str) -> list[Pipeline]:
        return [p for p in self.pipelines.values() if p.domain == domain]

    def get_state(self, pipeline_id: str) -> PipelineState:
        return self.pipelines[pipeline_id].state
```

---

## Example Pipelines

### AI Arena

```python
arena_pipeline = Pipeline(
    id="ai-arena",
    name="AI Arena Multi-Agent Debate",
    domain="commandcentral",
    stages=[
        Stage(id="preflight", name="Pre-flight Check",
              executor=PreflightExecutor(),
              on_failure=FailurePolicy.FAIL_LOUD,
              required=True),
        Stage(id="round-1", name="Initial Responses",
              executor=AgentRoundExecutor(round=1),
              on_failure=FailurePolicy.FAIL_LOUD,
              required=True),
        Stage(id="round-2", name="Rebuttals",
              executor=AgentRoundExecutor(round=2),
              on_failure=FailurePolicy.ASK_USER,
              required=False),
        Stage(id="consensus", name="Consensus Extraction",
              executor=ConsensusExecutor(),
              on_failure=FailurePolicy.FAIL_LOUD,
              required=True),
        Stage(id="capture", name="Knowledge Capture",
              executor=KnowledgeCaptureExecutor(),
              on_failure=FailurePolicy.FAIL_LOUD,
              required=True),
    ],
    config=PipelineConfig(
        required_participants=["claude", "gpt", "grok", "kimi"],
        pre_flight_check=True,
        require_pre_flight_pass=True
    )
)
```

### UX/UI Validation

```python
ux_pipeline = Pipeline(
    id="ux-validation",
    name="UX/UI Validation Pipeline",
    domain="cc4",
    stages=[
        Stage(id="spec-parse", name="Spec Parsing", ...),
        Stage(id="component-gen", name="Component Generation", ...),
        Stage(id="accessibility", name="Accessibility Check", ...),
        Stage(id="visual-review", name="Visual Review", ...),
    ],
    config=PipelineConfig(
        self_configuring=True,
        knowledge_sources=["ux-patterns", "component-library"],
        skill_sources=["ux-skills"]
    )
)
```

### Knowledge Radar (Wildvine)

```python
radar_pipeline = Pipeline(
    id="knowledge-radar",
    name="Knowledge Ingestion Radar",
    domain="wildvine",
    stages=[
        Stage(id="scan", name="Source Scan", ...),
        Stage(id="extract", name="Content Extraction", ...),
        Stage(id="synthesize", name="Synthesis", ...),
        Stage(id="output-md", name="Write Markdown", ...),
        Stage(id="output-kb", name="Index to KB", ...),
    ]
)
```

### The Vine (Product Ideation)

```python
vine_pipeline = Pipeline(
    id="the-vine-ideation",
    name="Product Ideation via Agent Discussion",
    domain="the-vine",
    stages=[
        Stage(id="seed", name="Seed Idea Input", ...),
        Stage(id="personas", name="Load Agent Personas", ...),
        Stage(id="discuss", name="Multi-Agent Discussion",
              config={"rounds": 3, "required_agents": ["all"]}),
        Stage(id="research", name="External Research",
              executors=["web-search", "youtube", "twitter"]),
        Stage(id="synthesize", name="Synthesis + Refinement", ...),
        Stage(id="human-steer", name="Human Steering Input", ...),
        Stage(id="capture", name="Knowledge Capture", ...),
    ],
    config=PipelineConfig(
        self_configuring=True,
        knowledge_sources=["product-patterns", "market-research"],
        on_required_missing=FailurePolicy.FAIL_LOUD
    )
)
```

---

## Self-Reconfiguration

Pipelines can reconfigure themselves based on accumulated knowledge/skills.

### Current State (UX Pipeline)

```python
# Minimal version - reads patterns, adjusts validation rules
class UXPipeline:
    async def reconfigure(self):
        patterns = await self.get_patterns()
        self.validation_rules = self.derive_rules(patterns)
```

### Extended Version (Target)

```python
class SelfConfiguringPipeline:
    """Full self-reconfiguration based on knowledge/skills."""

    async def watch_knowledge(self):
        """React to knowledge changes."""
        async for change in self.kb.watch(self.knowledge_sources):
            await self.handle_knowledge_change(change)

    async def handle_knowledge_change(self, change: KnowledgeChange):
        match change.type:
            case "new_pattern":
                # New pattern discovered - might need new stage
                await self.propose_new_stage(change.pattern)

            case "skill_added":
                # New skill available - can we use it?
                await self.integrate_skill(change.skill)

            case "skill_deprecated":
                # Skill no longer recommended
                await self.remove_skill_usage(change.skill)

            case "conflict_detected":
                # Two skills conflict
                await self.resolve_conflict(change.skills)

    async def propose_new_stage(self, pattern: Pattern):
        """Propose adding a new pipeline stage - never auto-apply."""

        stage = self.generate_stage(pattern)
        position = self.find_optimal_position(stage)

        proposal = StageAdditionProposal(
            stage=stage,
            position=position,
            rationale=f"New pattern '{pattern.name}' suggests this capability",
            impact=self.analyze_impact(stage)
        )

        # User decides - never auto-apply
        await self.submit_proposal(proposal)
```

---

## Pipeline Visualization

### Requirements

1. **See all pipelines** - What exists across all services
2. **See pipeline state** - Running, idle, failed, waiting
3. **See stage state** - Which stage is active, which passed/failed
4. **See connections** - How pipelines feed into each other
5. **Modify pipelines** - Add/remove/reorder stages
6. **Modify config** - Change failure policies, participants, sources

### Visualization Data Model

```python
@dataclass
class PipelineVisualization:
    """Everything needed to render a pipeline."""

    # Identity
    id: str
    name: str
    domain: str

    # Structure
    stages: list[StageVisualization]
    connections: list[Connection]  # To other pipelines

    # State
    status: Literal["idle", "running", "paused", "failed", "complete"]
    current_stage: Optional[str]
    progress: float  # 0-1

    # History
    last_run: datetime
    run_count: int
    success_rate: float

    # Configuration
    config: PipelineConfig
    is_self_configuring: bool
    pending_proposals: list[Proposal]

@dataclass
class StageVisualization:
    id: str
    name: str
    status: Literal["pending", "running", "success", "failed", "skipped"]
    executor_type: str
    duration: Optional[timedelta]
    error: Optional[str]

    # For modification
    can_remove: bool
    can_reorder: bool
    position: int
```

### Visualization API

```python
class PipelineVisualizationAPI:
    """API for pipeline visualization UI."""

    # Read
    async def get_all_pipelines(self) -> list[PipelineVisualization]:
        """Get all pipelines across all services."""

    async def get_pipeline(self, id: str) -> PipelineVisualization:
        """Get single pipeline with full detail."""

    async def get_pipeline_history(self, id: str) -> list[PipelineRun]:
        """Get execution history."""

    # Modify
    async def add_stage(self, pipeline_id: str, stage: Stage, position: int):
        """Add stage to pipeline."""

    async def remove_stage(self, pipeline_id: str, stage_id: str):
        """Remove stage from pipeline."""

    async def reorder_stages(self, pipeline_id: str, order: list[str]):
        """Reorder pipeline stages."""

    async def update_config(self, pipeline_id: str, config: PipelineConfig):
        """Update pipeline configuration."""

    # Control
    async def run(self, pipeline_id: str, input: Any):
        """Run pipeline with input."""

    async def pause(self, pipeline_id: str):
        """Pause running pipeline."""

    async def resume(self, pipeline_id: str):
        """Resume paused pipeline."""

    async def cancel(self, pipeline_id: str):
        """Cancel running pipeline."""
```

### UI Approach: Hybrid

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE DASHBOARD                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    PIPELINE OVERVIEW (VISLZR)                    │    │
│  │                                                                   │    │
│  │    [AI Arena]──────►[Knowledge Capture]──────►[KB Index]         │    │
│  │         │                                          │              │    │
│  │         ▼                                          ▼              │    │
│  │    [The Vine]◄─────────────────────────────[Repo Agent]          │    │
│  │         │                                          │              │    │
│  │         ▼                                          ▼              │    │
│  │    [UX Pipeline]──────►[Component Gen]──────►[Validation]        │    │
│  │                                                                   │    │
│  │    Click any pipeline to edit...                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    PIPELINE EDITOR                               │    │
│  │                                                                   │    │
│  │  [AI Arena] ════════════════════════════════════════════════     │    │
│  │                                                                   │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │    │
│  │  │Preflight│→│ Round 1 │→│ Round 2 │→│Consensus│→│ Capture│ │    │
│  │  │  ✓      │  │  ✓      │  │  ●      │  │  ○      │  │  ○     │ │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └────────┘ │    │
│  │                                                                   │    │
│  │  Config:                                                          │    │
│  │  ├─ Required: [Claude ✓] [GPT ✓] [Grok ✓] [Kimi ✗]              │    │
│  │  ├─ On Missing: [FAIL_LOUD ▼]                                    │    │
│  │  └─ Pre-flight: [Required ✓]                                     │    │
│  │                                                                   │    │
│  │  [+ Add Stage]  [Run]  [Save]                                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

- **VISLZR Canvas**: For viewing/exploring pipeline relationships
- **Dedicated Editor**: For modifying stages, config, failure policies
- **Same data model** underlies both

---

## Implementation Priority

### Phase 1: Universal Pipeline Model
- Define Pipeline/Stage/Config data structures
- Create PipelineRegistry
- Migrate AI Arena to model

### Phase 2: Pre-flight and Intent Enforcement
- Pre-flight checks for all pipelines
- FAIL_LOUD as default
- Test all participants before running

### Phase 3: Self-Reconfiguration
- Extend UX Pipeline pattern to all pipelines
- Knowledge/skill change watchers
- Proposal system for changes

### Phase 4: Visualization
- Pipeline API
- VISLZR integration for overview
- Dedicated editor for modification

### Phase 5: Cross-Service
- Pipelines spanning multiple services
- Wildvine/The Vine pipelines
- Cross-service visibility

---

## Open Questions

1. **Pipeline Registry Location**: Central (CommandCentral) or per-service with aggregation?
2. **Modification Permissions**: Who can modify which pipelines?
3. **Cross-Service Pipelines**: Can a pipeline span CC4 + Wildvine + The Vine?
4. **Version Control**: Should pipeline configs be git-tracked?
5. **Rollback**: How to rollback a bad reconfiguration?

---

*"If it has stages and flows, it's a pipeline. Treat it as one."*
