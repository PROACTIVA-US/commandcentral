# Skills & Knowledge Distribution Architecture

## Problem Statement

The CC4 monolith is being split into 4 microservices:
- **CommandCentral** (port 8000): Auth, projects, decisions, audit, entity state
- **PIPELZR** (port 8001): Tasks, pipelines, agents, skills
- **VISLZR** (port 8002): Canvas, nodes, relationships, exploration
- **IDEALZR** (port 8003): Goals, hypotheses, evidence, forecasts, ideas

**Critical Issue:** CC4 currently contains all the "intelligence" needed to execute work:
1. Spec extraction from markdown documents
2. Task dependency analysis and batching
3. Git worktree management for parallel execution
4. Agent orchestration with Claude
5. Code generation with domain knowledge
6. Failure recovery and retry logic
7. PR creation and merge automation

When we tried to build the CommandCentral frontend using CC4's pipeline system, the agents failed because:
- They were executing in CC4's repo context, not CommandCentral
- The agents had knowledge of CC4's architecture, not CommandCentral's
- No domain-specific skills/knowledge existed for CommandCentral

## Core Question

**Where should the skills and knowledge live in the split architecture?**

### Option A: PIPELZR Owns All Pipeline Intelligence

PIPELZR becomes the "brain" that orchestrates work across all services:

```
PIPELZR (port 8001)
├── /specs/                 # Spec documents for all services
├── /skills/                # Skills for all domains
│   ├── commandcentral/     # CC domain skills
│   ├── idealzr/            # Strategy domain skills
│   ├── vislzr/             # Visualization domain skills
│   └── pipelzr/            # Meta: pipeline domain skills
├── /knowledge/             # Domain knowledge bases
└── /agents/                # Agent configurations
```

**Pros:**
- Single source of truth for execution capability
- Unified pipeline monitoring
- Consistent agent behavior

**Cons:**
- PIPELZR becomes a bottleneck
- Each service can't evolve independently
- Tight coupling through knowledge requirements

### Option B: Each Service Owns Its Own Skills

Each service contains the skills needed to build/modify itself:

```
CommandCentral/
├── /skills/           # Skills for CommandCentral development
├── /knowledge/        # Domain knowledge about auth, projects, etc.
└── /specs/            # Specs for CommandCentral features

PIPELZR/
├── /skills/           # Skills for PIPELZR development
├── /knowledge/        # Domain knowledge about tasks, pipelines
├── /orchestration/    # The execution engine (shared across services)
└── /specs/

VISLZR/
├── /skills/
├── /knowledge/
└── /specs/

IDEALZR/
├── /skills/
├── /knowledge/
└── /specs/
```

**Pros:**
- Services are self-contained
- Can evolve independently
- Domain experts can maintain their own skills

**Cons:**
- Duplication of base skills
- Cross-service work requires coordination
- Multiple places to update shared patterns

### Option C: Federated Skills with Central Registry

PIPELZR maintains the execution engine and a registry, but skills are distributed:

```
PIPELZR (Orchestrator)
├── /orchestration/        # Execution engine
├── /registry/             # Points to skills in other services
│   └── skills.json        # {"commandcentral": "http://8000/skills", ...}
└── /core-skills/          # Shared patterns (git, testing, etc.)

CommandCentral
├── /skills/               # Self-knowledge
└── /knowledge/

(Each service exposes its skills via API)
```

**Pros:**
- Best of both worlds
- Services own their domain knowledge
- Central orchestration remains unified

**Cons:**
- More complex architecture
- Network calls for skill resolution
- Requires skill API specification

## Immediate Decision Needed

To build the CommandCentral frontend, we need:

1. **Skills** that understand:
   - CommandCentral's backend API structure (port 8000)
   - React + TypeScript + Tailwind + shadcn patterns
   - How to integrate with the other 3 services
   - Authentication flow with JWT

2. **Knowledge** about:
   - CommandCentral's domain model (projects, decisions, audit, etc.)
   - The federated auth pattern
   - Cross-service communication

3. **Execution capability** that can:
   - Create files in CommandCentral repo (not CC4)
   - Run npm commands in the right context
   - Create branches and PRs in CommandCentral

## Recommendation

**Short term (now):** Run the pipeline from CC4 but configure it to:
- Target CommandCentral repo explicitly (`repo_url: file:///...CommandCentral`)
- Use CommandCentral-specific skills (need to create these)
- Generate code for the CommandCentral domain

**Medium term:** Migrate pipeline execution capability to PIPELZR with Option C (federated skills)

**Long term:** Each service maintains its own skills, PIPELZR provides the execution engine

## Action Items

- [ ] Create `/skills/commandcentral/` directory structure in PIPELZR or CC4
- [ ] Define skill manifest for CommandCentral frontend development
- [ ] Create domain knowledge document for CommandCentral
- [ ] Configure pipeline to correctly target CommandCentral repo
- [ ] Test with a simple task before re-running full frontend build

## Questions for Resolution

1. Should we complete the microservice split before building the frontend?
2. Is PIPELZR ready to be the orchestrator, or does it need the same frontend work?
3. Should all 4 frontends share a common component library, or be independent?
4. How do we handle cross-service features (global search, activity feed)?
