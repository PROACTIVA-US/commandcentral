# CommandCentral Backend

**Governance & Truth State Service** for the CommandCentral Platform.

The central authority for state machines, permissions, audit logging, decision primitives, and cross-service coordination.

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Run the server
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/health` | Health check |
| `/metrics` | Service metrics |
| `/api/v1/auth` | Authentication (login, register) |
| `/api/v1/state-machine` | State machine operations |
| `/api/v1/decisions` | Decision primitives |
| `/api/v1/events` | Event streaming |
| `/api/v1/projects` | Project management |

## Architecture

CommandCentral is one of four services in the platform:

```
┌─────────────────────────────────────────────────────────────┐
│                  CommandCentral Platform                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ COMMANDCENT │  │  PIPELZR │  │  VISLZR  │  │  IDEALZR │ │
│  │   (8000)    │  │  (8001)  │  │  (8002)  │  │  (8003)  │ │
│  │             │  │          │  │          │  │          │ │
│  │ Governance  │  │ Pipelines│  │ Visual   │  │ Strategy │ │
│  │ State       │  │ Execution│  │ Kanban   │  │ Goals    │ │
│  │ Permissions │  │ Ingestion│  │ Dashoard │  │ Ideas    │ │
│  │ Audit       │  │ Workflows│  │          │  │ Insights │ │
│  └─────────────┘  └──────────┘  └──────────┘  └──────────┘ │
│         │              │             │             │        │
│         └──────────────┴─────────────┴─────────────┘        │
│                         Events Bus                          │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
backend/
├── app/
│   ├── main.py           # Application entry point
│   ├── config.py         # Configuration management
│   ├── database.py       # Database setup (SQLAlchemy async)
│   ├── models/           # SQLAlchemy models
│   │   ├── user.py
│   │   ├── audit.py
│   │   ├── decision.py
│   │   ├── project.py
│   │   └── entity_state.py
│   ├── routers/          # API endpoints
│   │   ├── auth.py
│   │   ├── health.py
│   │   ├── state_machine.py
│   │   ├── decisions.py
│   │   ├── events.py
│   │   └── projects.py
│   ├── services/         # Business logic
│   │   ├── auth_service.py
│   │   ├── audit_service.py
│   │   ├── decision_service.py
│   │   └── project_service.py
│   ├── middleware/       # HTTP middleware
│   │   ├── logging.py
│   │   ├── rate_limit.py
│   │   ├── metrics.py
│   │   └── correlation.py
│   └── schemas/          # Pydantic schemas
│       ├── common.py
│       ├── auth.py
│       ├── state_machine.py
│       ├── decisions.py
│       └── projects.py
├── data/                 # SQLite database (dev)
├── tests/                # Test suite
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Format code
black app tests
ruff check app tests --fix
```

## Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT signing key (change in production!)
- `DEBUG`: Enable debug mode
- `CORS_ORIGINS`: Allowed CORS origins

## License

MIT
