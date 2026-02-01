---
title: Service Self-Documentation Standard
version: 1.0.0
created: 2026-01-31
status: active
---

# Service Self-Documentation Standard

Every microservice in the CC4 ecosystem MUST include a `/docs/service-spec/` directory that describes the service for autonomous agents and other services.

## Required Structure

```
/docs/service-spec/
├── api-reference.md       # All endpoints with request/response schemas
├── domain-model.md        # Core entities and relationships
├── patterns.md            # Coding conventions and patterns
├── dependencies.md        # External dependencies and versions
└── skills/
    ├── manifest.json      # Index of all skills
    └── [skill-name].yaml  # Individual skill definitions
```

## File Specifications

### api-reference.md

Must contain:
- Base URL and port
- Authentication requirements
- All endpoints grouped by resource
- Request/response examples with TypeScript types
- Error codes and handling

Example format:
```markdown
## Authentication

All endpoints require Bearer token in Authorization header.

## Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/login | Authenticate user |
| POST | /api/v1/auth/register | Create new user |
| GET | /api/v1/auth/me | Get current user |

#### POST /api/v1/auth/login

Request:
```json
{
  "email": "string",
  "password": "string"
}
```

Response:
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```
```

### domain-model.md

Must contain:
- List of all entities with their purpose
- Entity relationships (1:1, 1:N, M:N)
- State machines with transitions
- Entity lifecycle documentation

Example format:
```yaml
entities:
  - name: Project
    purpose: "Primary isolation boundary across all services"
    fields:
      - name: id (UUID)
      - name: slug (string, unique)
      - state: ProjectState enum
    relationships:
      - has_many: decisions
      - has_many: team_members (Users)
    state_machine:
      states: [proposed, active, paused, completed, killed]
      transitions:
        proposed: [active, killed]
        active: [paused, completed, killed]
        paused: [active, killed]
        completed: []
        killed: []
```

### patterns.md

Must contain:
- Tech stack (frameworks, libraries)
- File organization conventions
- Naming conventions
- Error handling patterns
- Testing patterns

### dependencies.md

Must contain:
- Runtime dependencies with versions
- Development dependencies
- External service dependencies
- Required environment variables

### skills/manifest.json

Index of all skills available in this service:
```json
{
  "version": "1.0.0",
  "service": "commandcentral",
  "skills": [
    {
      "name": "auth-frontend",
      "file": "auth-frontend.yaml",
      "category": "frontend",
      "triggers": ["login", "register", "auth"]
    }
  ]
}
```

## Usage by PIPELZR

When PIPELZR receives a task:

1. Extract target service from task context
2. Fetch `/docs/service-spec/manifest.json` from target service (or local path)
3. Match task to skills using trigger patterns
4. Load matching skill definitions
5. Fetch domain-model.md and api-reference.md as context
6. Execute task with skill + knowledge

## Validation

Services SHOULD validate their self-documentation:
- All API endpoints documented
- All models documented
- All skills have valid YAML
- No broken internal links

## Updates

Self-documentation MUST be updated when:
- New endpoints are added
- Models change
- Patterns change
- New skills are created
