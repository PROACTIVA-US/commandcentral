---
title: CommandCentral Domain Model
version: 1.0.0
updated: 2026-01-31
service: commandcentral
---

# CommandCentral Domain Model

## Overview

CommandCentral is the **governance layer** for the CC4 microservices ecosystem. It owns:

- **Authentication & Authorization**: User accounts, roles, permissions
- **Projects**: The primary isolation boundary spanning all services
- **Decisions**: Governed decision-making with state machines
- **Audit Trail**: Immutable log of all state changes and actions
- **Cross-Service State**: Centralized state tracking for entities in other services

---

## Entities

### User

Authentication identity with roles and permissions.

```yaml
entity: User
table: users
purpose: Authentication and authorization identity

fields:
  id: string (UUID, primary key)
  email: string (unique, indexed)
  hashed_password: string
  name: string (optional)
  avatar_url: string (optional)
  is_active: boolean (default: true)
  is_superuser: boolean (default: false)
  roles: string[] (e.g., ["admin", "user", "viewer"])
  permissions: Record<string, boolean>
  project_ids: string[] (projects user has access to)
  active_project_id: string (optional, current context)
  created_at: datetime
  updated_at: datetime
  last_login_at: datetime (optional)

methods:
  has_role(role: string) -> boolean
  has_permission(permission: string) -> boolean
```

### Project

The primary isolation boundary across all services.

```yaml
entity: Project
table: projects
purpose: Container for all work, spans all services

fields:
  id: string (UUID, primary key)
  name: string
  slug: string (unique, indexed, URL-safe)
  description: string (optional)
  state: ProjectState enum
  state_changed_at: datetime
  state_changed_by: string (user_id)
  owner_id: string (user_id, required)
  team_ids: string[] (list of user_ids)
  settings: JSON object
  extra_data: JSON object (renamed from 'metadata')
  repo_path: string (optional, local path for PIPELZR)
  repo_url: string (optional, remote URL)
  created_at: datetime
  updated_at: datetime

state_machine:
  name: ProjectState
  states:
    - proposed: Initial state for new projects
    - active: Project is being worked on
    - paused: Temporarily suspended
    - completed: Successfully finished (terminal)
    - killed: Abandoned/cancelled (terminal)

  transitions:
    proposed -> active: "Activate project"
    proposed -> killed: "Kill before starting"
    active -> paused: "Pause work"
    active -> completed: "Mark as done"
    active -> killed: "Abandon project"
    paused -> active: "Resume work"
    paused -> killed: "Abandon while paused"

relationships:
  belongs_to: User (owner)
  has_many: Users (team_members via team_ids)
  has_many: Decisions
  has_many: EntityStates (for cross-service entities)
  has_many: AuditEntries

methods:
  can_transition_to(new_state: ProjectState) -> boolean
  allowed_transitions() -> ProjectState[]
```

### Decision

Governed decision primitive with state machine.

```yaml
entity: Decision
table: decisions
purpose: Structured decision-making with governance

fields:
  id: string (UUID, primary key)
  project_id: string (foreign key -> projects.id, indexed)
  title: string
  question: string (optional, required for activation)
  context: string (optional, background information)
  options: JSON array (list of option objects)
  selected_option: string (optional, set when decided)
  rationale: string (optional, set when decided)
  state: DecisionState enum
  state_changed_at: datetime
  state_changed_by: string (user_id)
  related_decision_ids: string[] (links to other decisions)
  related_hypothesis_ids: string[] (links to IDEALZR)
  related_evidence_ids: string[] (links to IDEALZR)
  tags: string[]
  extra_data: JSON object
  created_at: datetime
  updated_at: datetime
  decided_at: datetime (optional)
  created_by: string (user_id)
  decided_by: string (optional, user_id)

option_schema:
  id: string
  label: string
  description: string (optional)
  pros: string[] (optional)
  cons: string[] (optional)

state_machine:
  name: DecisionState
  states:
    - draft: Being prepared, not ready for decision
    - active: Ready for decision, collecting input
    - decided: Decision has been made (terminal for changes)
    - archived: Closed and archived (terminal)

  transitions:
    draft -> active: "Activate for decision"
    active -> decided: "Make decision"
    active -> archived: "Archive without deciding"
    decided -> archived: "Archive after decision"

  transition_requirements:
    draft -> active:
      - question: required
      - options: required (at least 2)
    active -> decided:
      - selected_option: required
      - rationale: recommended

relationships:
  belongs_to: Project
  created_by: User
  decided_by: User (optional)

methods:
  can_transition_to(new_state: DecisionState) -> boolean
  allowed_transitions() -> DecisionState[]
  check_transition_requirements(new_state) -> (bool, missing_fields[])
```

### AuditEntry

Immutable audit log entry for compliance and debugging.

```yaml
entity: AuditEntry
table: audit_entries
purpose: Immutable log of all state changes and actions

fields:
  id: string (UUID, primary key)
  event_type: AuditEventType enum (indexed)
  event_name: string (e.g., "decision.activate")
  entity_type: string (optional, indexed)
  entity_id: string (optional, indexed)
  actor_type: string ("user", "system", "service")
  actor_id: string (optional, indexed)
  from_state: string (optional)
  to_state: string (optional)
  transition_name: string (optional)
  success: boolean
  failure_reason: string (optional)
  project_id: string (optional, indexed)
  correlation_id: string (optional, for request tracing)
  rationale: string (optional)
  extra_data: JSON object
  side_effects: JSON array (what else happened)
  timestamp: datetime (indexed)

event_types:
  # State machine events
  - transition_attempt
  - transition_success
  - transition_denied

  # Permission events
  - permission_check
  - permission_granted
  - permission_denied

  # Entity events
  - entity_created
  - entity_updated
  - entity_deleted

  # Auth events
  - auth_login
  - auth_logout
  - auth_failed

  # Cross-service events
  - service_call
  - service_event

  # System events
  - system_event
  - error

factory_methods:
  create_transition_attempt(entity_type, entity_id, from_state, to_state, ...)
  create_permission_check(permission, granted, actor_id, ...)

immutability:
  - Once created, audit entries cannot be modified or deleted
  - This provides a complete trail for governance and compliance
```

### EntityState

Generic state tracking for cross-service entities.

```yaml
entity: EntityState
table: entity_states
purpose: Track state for entities in other services (PIPELZR, IDEALZR, VISLZR)

fields:
  id: string (UUID, primary key)
  entity_type: string (indexed, e.g., "task", "hypothesis")
  entity_id: string (indexed)
  service: string (e.g., "pipelzr", "idealzr")
  current_state: string
  state_machine_id: string (optional, reference to config)
  project_id: string (optional, indexed)
  last_transition_at: datetime
  last_transition_by: string (user_id or service)
  last_transition_from: string (optional)
  allowed_transitions: string[] (cached from state machine)
  extra_data: JSON object
  created_at: datetime
  updated_at: datetime

unique_constraint:
  - (entity_type, entity_id, service)

purpose:
  - Allows CommandCentral to manage state machines for entities that live in other services
  - PIPELZR tasks, IDEALZR hypotheses, etc. can have their state tracked centrally
  - Enables cross-service governance policies
```

---

## Entity Relationships

```
┌─────────────┐     owns      ┌─────────────┐
│    User     │──────────────>│   Project   │
└─────────────┘               └─────────────┘
      │                             │
      │ member_of                   │ has_many
      │                             │
      ▼                             ▼
┌─────────────┐               ┌─────────────┐
│   Project   │<──────────────│  Decision   │
│  (team_ids) │  belongs_to   └─────────────┘
└─────────────┘                     │
      │                             │
      │ has_many                    │ creates
      │                             │
      ▼                             ▼
┌─────────────┐               ┌─────────────┐
│ EntityState │               │ AuditEntry  │
│(cross-svc)  │               └─────────────┘
└─────────────┘
```

---

## State Machine Diagrams

### Project Lifecycle

```
                    ┌──────────┐
                    │ proposed │
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         activate       kill       kill
              │          │          │
              ▼          ▼          │
         ┌────────┐  ┌────────┐    │
         │ active │  │ killed │◄───┘
         └───┬────┘  └────────┘
             │
    ┌────────┼────────┬────────┐
    │        │        │        │
  pause  complete   kill      │
    │        │        │        │
    ▼        ▼        ▼        │
┌────────┐ ┌───────────┐ ┌────────┐
│ paused │ │ completed │ │ killed │
└───┬────┘ └───────────┘ └────────┘
    │
    │ resume / kill
    │
    ▼
  active / killed
```

### Decision Lifecycle

```
┌─────────┐
│  draft  │
└────┬────┘
     │
  activate (requires question + options)
     │
     ▼
┌─────────┐
│ active  │
└────┬────┘
     │
     ├───── decide (requires selected_option) ──────► ┌─────────┐
     │                                                │ decided │
     │                                                └────┬────┘
     │                                                     │
     └───── archive ──────────────────────────────────────►│
                                                           ▼
                                                     ┌──────────┐
                                                     │ archived │
                                                     └──────────┘
```

---

## Cross-Service Integration

CommandCentral serves as the governance hub. Other services interact via:

1. **Project Context**: All entities in PIPELZR, IDEALZR, VISLZR belong to a project
2. **State Tracking**: EntityState table tracks state of external entities
3. **Audit Trail**: All significant actions are logged in AuditEntry
4. **Events**: CommandCentral emits events for cross-service coordination

### Service Interactions

| Service | CommandCentral Provides | CommandCentral Receives |
|---------|------------------------|------------------------|
| PIPELZR | Project context, Task state tracking | Task state updates, Execution events |
| IDEALZR | Project context, Goal/Hypothesis linking | Goal updates, Evidence events |
| VISLZR | Project context, Entity relationships | Canvas events, Node creation |
