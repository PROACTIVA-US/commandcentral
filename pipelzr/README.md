# PIPELZR

**Codebase & Execution Service** for the CommandCentral Platform.

## Overview

PIPELZR is the execution engine that handles:

- **Task Execution**: Run tasks locally, in Dagger containers, or in E2B sandboxes
- **Pipeline Orchestration**: Batch and parallel task execution with dependency management
- **Agent Session Management**: AI agent lifecycle and conversation handling
- **Skill Execution**: Reusable capability invocation
- **Codebase Indexing**: Code analysis and search

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          PIPELZR                                │
│                   (Port 8000, mapped to 8001)                   │
├─────────────────────────────────────────────────────────────────┤
│  API Layer                                                      │
│  ├── /api/v1/tasks      - Task CRUD and execution              │
│  ├── /api/v1/agents     - Agent session management             │
│  ├── /api/v1/pipelines  - Pipeline orchestration               │
│  ├── /api/v1/skills     - Skill registry and invocation        │
│  ├── /health            - Health check                          │
│  └── /metrics           - Service metrics                       │
├─────────────────────────────────────────────────────────────────┤
│  Service Layer                                                  │
│  ├── TaskService        - Task lifecycle and execution         │
│  ├── AgentService       - Agent session handling               │
│  └── PipelineService    - Pipeline orchestration               │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer                                                     │
│  ├── Task               - Executable unit of work              │
│  ├── Agent              - AI agent session                     │
│  ├── Pipeline           - Task workflow                        │
│  └── Skill              - Reusable capability                  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Run development server
uvicorn app.main:app --reload --port 8000

# Or use the CLI entry point
python -m app.main
```

### Docker

```bash
# Build and run with docker-compose (from CommandCentral root)
docker-compose up pipelzr
```

## API Endpoints

### Health

- `GET /health` - Basic health check
- `GET /ready` - Readiness check with backend status
- `GET /metrics` - Service metrics

### Tasks

- `POST /api/v1/tasks` - Create a task
- `GET /api/v1/tasks` - List tasks
- `GET /api/v1/tasks/{id}` - Get task details
- `POST /api/v1/tasks/{id}/execute` - Execute a task
- `POST /api/v1/tasks/{id}/cancel` - Cancel a task
- `POST /api/v1/tasks/{id}/retry` - Retry a failed task

### Agents

- `POST /api/v1/agents` - Create an agent session
- `GET /api/v1/agents` - List agents
- `GET /api/v1/agents/{id}` - Get agent details
- `POST /api/v1/agents/{id}/initialize` - Initialize agent
- `POST /api/v1/agents/{id}/message` - Send message to agent
- `POST /api/v1/agents/{id}/pause` - Pause agent
- `POST /api/v1/agents/{id}/resume` - Resume agent
- `POST /api/v1/agents/{id}/terminate` - Terminate agent

### Pipelines

- `POST /api/v1/pipelines` - Create a pipeline
- `GET /api/v1/pipelines` - List pipelines
- `GET /api/v1/pipelines/{id}` - Get pipeline details
- `POST /api/v1/pipelines/{id}/start` - Start a pipeline
- `POST /api/v1/pipelines/{id}/execute` - Execute entire pipeline
- `POST /api/v1/pipelines/{id}/pause` - Pause pipeline
- `POST /api/v1/pipelines/{id}/resume` - Resume pipeline
- `POST /api/v1/pipelines/{id}/cancel` - Cancel pipeline
- `POST /api/v1/pipelines/{id}/retry` - Retry failed pipeline

### Skills

- `POST /api/v1/skills` - Create a skill
- `GET /api/v1/skills` - List skills
- `GET /api/v1/skills/{id}` - Get skill details
- `PATCH /api/v1/skills/{id}` - Update a skill
- `DELETE /api/v1/skills/{id}` - Delete a skill
- `POST /api/v1/skills/{id}/invoke` - Invoke a skill

## Configuration

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port (8001 via docker-compose) |
| `DATABASE_URL` | sqlite:///./data/pipelzr.db | Database connection |
| `COMMANDCENTRAL_URL` | http://localhost:8000 | CommandCentral service URL |
| `DAGGER_ENABLED` | false | Enable Dagger execution |
| `E2B_ENABLED` | false | Enable E2B sandbox execution |
| `MAX_CONCURRENT_AGENTS` | 10 | Max concurrent agent sessions |
| `MAX_CONCURRENT_PIPELINES` | 5 | Max concurrent pipelines |

## Inter-Service Communication

PIPELZR communicates with:

- **CommandCentral** (port 8000): For project info, permissions, audit logging
- **VISLZR** (port 8002): For visualization updates
- **IDEALZR** (port 8003): For idea/hypothesis tracking

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Format code
black app/
ruff check app/ --fix

# Type checking (optional)
mypy app/
```

## License

MIT License - See LICENSE file for details.
