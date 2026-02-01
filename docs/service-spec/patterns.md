---
title: CommandCentral Coding Patterns
version: 1.0.0
updated: 2026-01-31
service: commandcentral
---

# CommandCentral Coding Patterns

## Backend Patterns

### Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | FastAPI | 0.109+ |
| Database | SQLite + SQLAlchemy | 2.0+ |
| ORM Mode | Async SQLAlchemy | - |
| Auth | JWT (python-jose) | - |
| Validation | Pydantic v2 | 2.0+ |
| Testing | pytest + pytest-asyncio | - |

### Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Settings via pydantic-settings
│   ├── database.py          # SQLAlchemy async setup
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── decision.py
│   │   ├── audit.py
│   │   └── entity_state.py
│   ├── routers/             # FastAPI routers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── decisions.py
│   │   ├── events.py
│   │   └── health.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── decisions.py
│   │   └── common.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── project_service.py
│   │   └── decision_service.py
│   └── middleware/          # Request processing
│       ├── __init__.py
│       ├── logging.py
│       ├── metrics.py
│       ├── rate_limit.py
│       └── correlation.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_projects.py
│   └── test_decisions.py
└── alembic/                 # Database migrations
```

### Router Pattern

```python
# routers/example.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services.example_service import ExampleService
from .auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[ExampleResponse])
async def list_examples(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """List all examples for current user."""
    service = ExampleService(session)
    return await service.list_all(user_id=current_user.id)

@router.post("/", response_model=ExampleResponse, status_code=status.HTTP_201_CREATED)
async def create_example(
    request: ExampleCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Create a new example."""
    service = ExampleService(session)
    return await service.create(
        user_id=current_user.id,
        **request.model_dump()
    )
```

### Service Pattern

```python
# services/example_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.example import Example
from ..models.audit import AuditEntry, AuditEventType

class ExampleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: str, **kwargs) -> Example:
        """Create with audit logging."""
        example = Example(created_by=user_id, **kwargs)
        self.session.add(example)

        # Log creation
        audit = AuditEntry(
            event_type=AuditEventType.ENTITY_CREATED,
            event_name="example.create",
            entity_type="example",
            entity_id=example.id,
            actor_type="user",
            actor_id=user_id,
        )
        self.session.add(audit)

        await self.session.commit()
        await self.session.refresh(example)
        return example

    async def transition(
        self,
        example_id: str,
        new_state: str,
        actor_id: str
    ) -> tuple[bool, str, Example | None]:
        """
        Transition state with validation and audit.

        Returns: (success, message, updated_example or None)
        """
        example = await self.get_by_id(example_id)
        if not example:
            return False, "Not found", None

        if not example.can_transition_to(new_state):
            # Log denied transition
            audit = AuditEntry.create_transition_attempt(
                entity_type="example",
                entity_id=example_id,
                from_state=example.state,
                to_state=new_state,
                actor_id=actor_id,
            )
            audit.success = False
            audit.failure_reason = f"Cannot transition from {example.state} to {new_state}"
            self.session.add(audit)
            await self.session.commit()
            return False, audit.failure_reason, example

        # Perform transition
        old_state = example.state
        example.state = new_state
        example.state_changed_by = actor_id

        # Log success
        audit = AuditEntry.create_transition_attempt(
            entity_type="example",
            entity_id=example_id,
            from_state=old_state,
            to_state=new_state,
            actor_id=actor_id,
        )
        audit.event_type = AuditEventType.TRANSITION_SUCCESS
        self.session.add(audit)

        await self.session.commit()
        return True, "Transition successful", example
```

### State Machine Pattern

```python
# In model files
import enum

class ExampleState(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"

# Valid transitions (from_state -> allowed_to_states)
EXAMPLE_TRANSITIONS = {
    ExampleState.DRAFT: [ExampleState.ACTIVE],
    ExampleState.ACTIVE: [ExampleState.COMPLETED],
    ExampleState.COMPLETED: [],  # Terminal
}

# In model class
def can_transition_to(self, new_state: ExampleState) -> bool:
    return new_state in EXAMPLE_TRANSITIONS.get(self.state, [])

def allowed_transitions(self) -> list[ExampleState]:
    return EXAMPLE_TRANSITIONS.get(self.state, [])
```

### Pydantic Response Pattern

```python
# schemas/example.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ExampleBase(BaseModel):
    title: str
    description: Optional[str] = None

class ExampleCreate(ExampleBase):
    """Request schema for creation."""
    pass

class ExampleUpdate(BaseModel):
    """Request schema for update (all fields optional)."""
    title: Optional[str] = None
    description: Optional[str] = None

class ExampleResponse(ExampleBase):
    """Response schema with computed fields."""
    id: str
    state: str
    created_at: datetime
    updated_at: datetime
    allowed_transitions: List[str]

    class Config:
        from_attributes = True
```

---

## Frontend Patterns (Planned)

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 18 + TypeScript |
| Build | Vite |
| Styling | Tailwind CSS |
| Components | shadcn/ui |
| State | Zustand |
| Data Fetching | TanStack Query |
| Routing | React Router v6 |
| Forms | react-hook-form + zod |

### File Structure

```
frontend/
├── src/
│   ├── api/                 # API clients
│   │   ├── baseClient.ts
│   │   ├── types.ts
│   │   └── clients/
│   │       ├── commandCentralClient.ts
│   │       ├── pipelzrClient.ts
│   │       ├── vislzrClient.ts
│   │       └── idealzrClient.ts
│   ├── components/
│   │   ├── common/          # Shared components
│   │   ├── layout/          # Layout components
│   │   ├── auth/            # Auth components
│   │   └── ui/              # shadcn components
│   ├── features/            # Feature modules
│   │   ├── commandcentral/
│   │   ├── pipelzr/
│   │   ├── vislzr/
│   │   └── idealzr/
│   ├── hooks/               # Custom hooks
│   ├── stores/              # Zustand stores
│   ├── pages/               # Page components
│   ├── routes/              # Router config
│   ├── styles/              # Global styles
│   └── types/               # TypeScript types
```

### Store Pattern

```typescript
// stores/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const { access_token } = await commandCentralClient.login(email, password);
        const user = await commandCentralClient.getMe();
        set({ token: access_token, user, isAuthenticated: true });
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
);
```

### API Client Pattern

```typescript
// api/baseClient.ts
import axios, { AxiosInstance } from 'axios';
import { useAuthStore } from '@/stores/authStore';

const SERVICE_URLS = {
  commandcentral: 'http://localhost:8000/api/v1',
  pipelzr: 'http://localhost:8001/api/v1',
  vislzr: 'http://localhost:8002/api/v1',
  idealzr: 'http://localhost:8003/api/v1',
} as const;

export function createServiceClient(service: keyof typeof SERVICE_URLS): AxiosInstance {
  const client = axios.create({
    baseURL: SERVICE_URLS[service],
  });

  // Add auth token
  client.interceptors.request.use((config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Handle 401
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        useAuthStore.getState().logout();
      }
      return Promise.reject(error);
    }
  );

  return client;
}
```

### Query Pattern

```typescript
// features/commandcentral/hooks/useProjects.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { commandCentralClient } from '@/api/clients/commandCentralClient';

export function useProjects(filters?: ProjectFilters) {
  return useQuery({
    queryKey: ['projects', filters],
    queryFn: () => commandCentralClient.getProjects(filters),
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: commandCentralClient.createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useProjectTransition(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (action: 'activate' | 'pause' | 'complete' | 'kill') =>
      commandCentralClient.transitionProject(projectId, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });
}
```

---

## Error Handling

### Backend Errors

```python
from fastapi import HTTPException, status

# Not found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found"
)

# Validation error
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid state transition"
)

# Auth error
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
```

### Frontend Errors

```typescript
// Wrap in error boundary
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

// Use toast for user feedback
import { toast } from 'sonner';

try {
  await mutateAsync(data);
  toast.success('Project created');
} catch (error) {
  toast.error('Failed to create project');
}
```

---

## Testing Patterns

### Backend Tests

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def client(session: AsyncSession):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def auth_headers(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# tests/test_projects.py
async def test_create_project(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Test Project"},
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"
    assert response.json()["state"] == "proposed"
```
