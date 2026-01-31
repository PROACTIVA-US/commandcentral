# CommandCentral Platform

> A distributed platform for intelligent project management, execution, and strategic planning with 4 microservices.

## Project Overview

**Type**: Python Multi-Service Platform (FastAPI)
**Status**: Active Development

## Architecture

| Service | Port | Purpose |
|---------|------|---------|
| **CommandCentral** (backend/) | 8000 | Governance, State, Permissions, Audit |
| **PIPELZR** (pipelzr/) | 8001 | Pipelines, Execution, Tasks, Agents |
| **VISLZR** (vislzr/) | 8002 | Visual Canvas, Graphs, Navigation |
| **IDEALZR** (idealzr/) | 8003 | Strategy, Goals, Ideas, Evidence |

## Key Commands

```bash
# Build/Run (Docker)
docker-compose up -d

# Run Individual Service (Development)
cd backend && uvicorn app.main:app --port 8000 --reload

# Test
cd backend && pytest

# Health Check
curl http://localhost:8000/health
```

## Current Focus

- [ ] Initial setup and GitHub remote configuration
- [ ] Architecture validation across services
- [ ] API endpoint implementation

## Code Style

- Python 3.11+
- FastAPI for all services
- Pydantic for schemas
- SQLAlchemy for database models
- Follow existing patterns in each service

## Important Files

- `README.md` - Project overview and quick start
- `ARCHITECTURE.md` - Detailed architecture documentation
- `docker-compose.yml` - Multi-service orchestration
- `backend/app/main.py` - CommandCentral entry point
- `docs/architecture/` - Architecture decision records

## Service Structure (Each Service)

```
service/
├── app/
│   ├── main.py        # FastAPI app entry
│   ├── config.py      # Configuration
│   ├── database.py    # DB connection
│   ├── models/        # SQLAlchemy models
│   ├── routers/       # API routes
│   ├── services/      # Business logic
│   ├── middleware/    # Request middleware
│   └── schemas/       # Pydantic schemas
├── data/              # Local data storage
├── requirements.txt
└── Dockerfile
```

## Notes

- Commit frequently with meaningful messages
- Each service runs independently on its own port
- Services communicate via HTTP APIs
- Ask before making architectural changes across services
