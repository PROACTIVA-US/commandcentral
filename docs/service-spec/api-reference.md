---
title: CommandCentral API Reference
version: 1.0.0
updated: 2026-01-31
service: commandcentral
port: 8000
---

# CommandCentral API Reference

**Base URL:** `http://localhost:8000/api/v1`

## Authentication

All endpoints except `/auth/login` and `/auth/register` require Bearer token authentication.

```http
Authorization: Bearer <access_token>
```

---

## Auth Endpoints

### POST /auth/register

Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "roles": [],
  "is_active": true
}
```

**Errors:**
- `400`: Email already registered

### POST /auth/login

Authenticate and receive access token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors:**
- `401`: Invalid credentials

### GET /auth/me

Get current authenticated user.

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "roles": ["user"],
  "is_active": true
}
```

### POST /auth/logout

Logout current user.

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

## Projects Endpoints

### GET /projects

List projects the user has access to.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| state | string | null | Filter by state |
| limit | int | 50 | Max results (max 100) |
| offset | int | 0 | Pagination offset |

**Response (200):**
```json
[
  {
    "id": "uuid",
    "name": "Project Name",
    "slug": "project-name",
    "description": "Description",
    "state": "active",
    "state_changed_at": "2026-01-31T10:00:00Z",
    "owner_id": "uuid",
    "team_ids": ["uuid"],
    "repo_path": "/path/to/repo",
    "repo_url": "https://github.com/org/repo",
    "settings": {},
    "metadata": {},
    "created_at": "2026-01-31T09:00:00Z",
    "updated_at": "2026-01-31T10:00:00Z",
    "allowed_transitions": ["paused", "completed", "killed"]
  }
]
```

### POST /projects

Create a new project.

**Request:**
```json
{
  "name": "New Project",
  "description": "Project description",
  "slug": "new-project",
  "repo_path": "/path/to/repo",
  "repo_url": "https://github.com/org/repo",
  "settings": {},
  "metadata": {}
}
```

**Response (201):** Project object

### GET /projects/{project_id}

Get project by ID.

**Response (200):** Project object

**Errors:**
- `404`: Project not found

### PUT /projects/{project_id}

Update project.

**Request:**
```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**Response (200):** Updated project object

### DELETE /projects/{project_id}

Delete project (only in PROPOSED state).

**Response (204):** No content

**Errors:**
- `400`: Cannot delete (not in proposed state)

### POST /projects/{project_id}/activate

Activate a proposed project.

**Response (200):**
```json
{
  "success": true,
  "message": "Project activated",
  "project": { ... }
}
```

### POST /projects/{project_id}/pause

Pause an active project.

**Request:**
```json
{
  "rationale": "Reason for pausing"
}
```

**Response (200):** TransitionResponse

### POST /projects/{project_id}/resume

Resume a paused project.

**Response (200):** TransitionResponse

### POST /projects/{project_id}/complete

Mark project as completed.

**Request:**
```json
{
  "rationale": "Completion notes"
}
```

**Response (200):** TransitionResponse

### POST /projects/{project_id}/kill

Kill a project.

**Request:**
```json
{
  "rationale": "Reason for killing"
}
```

**Response (200):** TransitionResponse

### GET /projects/{project_id}/transitions

Get allowed transitions for project.

**Response (200):**
```json
{
  "current_state": "active",
  "allowed_transitions": ["paused", "completed", "killed"]
}
```

### GET /projects/{project_id}/audit

Get audit trail for project.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 50 | Max results (max 100) |

**Response (200):**
```json
{
  "project_id": "uuid",
  "entries": [
    {
      "id": "uuid",
      "event_type": "transition_success",
      "event_name": "project.activate",
      "entity_type": "project",
      "entity_id": "uuid",
      "from_state": "proposed",
      "to_state": "active",
      "actor_id": "uuid",
      "success": true,
      "failure_reason": null,
      "timestamp": "2026-01-31T10:00:00Z"
    }
  ]
}
```

### POST /projects/{project_id}/team

Add team member.

**Request:**
```json
{
  "user_id": "uuid"
}
```

**Response (200):** Updated project object

### DELETE /projects/{project_id}/team/{user_id}

Remove team member.

**Response (200):** Updated project object

---

## Decisions Endpoints

### GET /decisions

List decisions for a project.

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| project_id | string | Yes | Filter by project |
| state | string | No | Filter by state |
| limit | int | No | Max results (default 50) |
| offset | int | No | Pagination offset |

**Response (200):**
```json
[
  {
    "id": "uuid",
    "project_id": "uuid",
    "title": "Decision Title",
    "question": "What should we decide?",
    "context": "Background context",
    "options": [
      {"id": "1", "label": "Option A", "description": "..."},
      {"id": "2", "label": "Option B", "description": "..."}
    ],
    "selected_option": null,
    "rationale": null,
    "state": "draft",
    "state_changed_at": "2026-01-31T10:00:00Z",
    "tags": ["architecture", "priority-high"],
    "created_at": "2026-01-31T09:00:00Z",
    "updated_at": "2026-01-31T10:00:00Z",
    "created_by": "uuid",
    "decided_by": null,
    "decided_at": null,
    "allowed_transitions": ["active"]
  }
]
```

### POST /decisions

Create a new decision.

**Request:**
```json
{
  "project_id": "uuid",
  "title": "Decision Title",
  "question": "What should we decide?",
  "context": "Background context",
  "options": [
    {"id": "1", "label": "Option A", "description": "..."},
    {"id": "2", "label": "Option B", "description": "..."}
  ],
  "tags": ["architecture"]
}
```

**Response (201):** Decision object

### GET /decisions/{decision_id}

Get decision by ID.

**Response (200):** Decision object

### PUT /decisions/{decision_id}

Update decision (draft or active only).

**Request:**
```json
{
  "title": "Updated Title",
  "question": "Updated question?",
  "options": [...]
}
```

**Response (200):** Updated decision object

### DELETE /decisions/{decision_id}

Delete decision (draft only).

**Response (204):** No content

### POST /decisions/{decision_id}/activate

Activate a draft decision.

**Preconditions:** Decision must have `question` and `options`.

**Response (200):** TransitionResponse

### POST /decisions/{decision_id}/decide

Make a decision.

**Request:**
```json
{
  "selected_option": "1",
  "rationale": "Why we chose this option"
}
```

**Response (200):** TransitionResponse

### POST /decisions/{decision_id}/archive

Archive a decision.

**Response (200):** TransitionResponse

### GET /decisions/{decision_id}/transitions

Get allowed transitions.

**Response (200):**
```json
{
  "current_state": "active",
  "allowed_transitions": ["decided", "archived"]
}
```

### GET /decisions/{decision_id}/audit

Get decision audit trail.

**Response (200):** Audit entries

---

## Health Endpoints

### GET /health

Health check.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "commandcentral",
  "version": "1.0.0"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400`: Bad request (validation error, invalid state transition)
- `401`: Unauthorized (missing or invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not found
- `500`: Internal server error

---

## TypeScript Types

```typescript
// Auth
interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
}

interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
}

interface UserResponse {
  id: string;
  email: string;
  name?: string;
  roles: string[];
  is_active: boolean;
}

// Projects
type ProjectState = 'proposed' | 'active' | 'paused' | 'completed' | 'killed';

interface Project {
  id: string;
  name: string;
  slug: string;
  description?: string;
  state: ProjectState;
  state_changed_at: string;
  owner_id: string;
  team_ids: string[];
  repo_path?: string;
  repo_url?: string;
  settings: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  allowed_transitions: ProjectState[];
}

interface TransitionResponse {
  success: boolean;
  message: string;
  project?: Project;
}

// Decisions
type DecisionState = 'draft' | 'active' | 'decided' | 'archived';

interface DecisionOption {
  id: string;
  label: string;
  description?: string;
}

interface Decision {
  id: string;
  project_id: string;
  title: string;
  question?: string;
  context?: string;
  options: DecisionOption[];
  selected_option?: string;
  rationale?: string;
  state: DecisionState;
  state_changed_at: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  created_by: string;
  decided_by?: string;
  decided_at?: string;
  allowed_transitions: DecisionState[];
}

// Audit
type AuditEventType =
  | 'transition_attempt'
  | 'transition_success'
  | 'transition_denied'
  | 'permission_check'
  | 'permission_granted'
  | 'permission_denied'
  | 'entity_created'
  | 'entity_updated'
  | 'entity_deleted'
  | 'auth_login'
  | 'auth_logout'
  | 'auth_failed'
  | 'service_call'
  | 'service_event'
  | 'system_event'
  | 'error';

interface AuditEntry {
  id: string;
  event_type: AuditEventType;
  event_name: string;
  entity_type?: string;
  entity_id?: string;
  from_state?: string;
  to_state?: string;
  actor_id?: string;
  success: boolean;
  failure_reason?: string;
  timestamp: string;
}
```
