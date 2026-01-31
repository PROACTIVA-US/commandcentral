# CommandCentral Platform

A distributed platform for intelligent project management, execution, and strategic planning.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CommandCentral Platform                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ CommandCent │  │ PIPELZR  │  │  VISLZR  │  │ IDEALZR  │                │
│  │   (8000)    │  │  (8001)  │  │  (8002)  │  │  (8003)  │                │
│  │             │  │          │  │          │  │          │                │
│  │ Governance  │  │ Pipelines│  │  Visual  │  │ Strategy │                │
│  │ State       │  │ Execution│  │  Canvas  │  │ Goals    │                │
│  │ Permissions │  │ Tasks    │  │  Wander  │  │ Ideas    │                │
│  │ Audit       │  │ Agents   │  │  Graphs  │  │ Evidence │                │
│  └─────────────┘  └──────────┘  └──────────┘  └──────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| **CommandCentral** | 8000 | Governance & Truth State - state machines, permissions, audit |
| **PIPELZR** | 8001 | Codebase & Execution - tasks, agents, pipelines |
| **VISLZR** | 8002 | Visualization & Exploration - canvas, graphs, navigation |
| **IDEALZR** | 8003 | Ideas & Strategic Intelligence - goals, hypotheses, evidence |

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Option 2: Local Development

```bash
# Terminal 1: CommandCentral
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload

# Terminal 2: PIPELZR
cd pipelzr && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload

# Terminal 3: VISLZR
cd vislzr && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8002 --reload

# Terminal 4: IDEALZR
cd idealzr && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8003 --reload
```

## API Documentation

Each service provides Swagger UI documentation:

- CommandCentral: http://localhost:8000/docs
- PIPELZR: http://localhost:8001/docs
- VISLZR: http://localhost:8002/docs
- IDEALZR: http://localhost:8003/docs

## Health Checks

```bash
# Check all services
curl http://localhost:8000/health  # CommandCentral
curl http://localhost:8001/health  # PIPELZR
curl http://localhost:8002/health  # VISLZR
curl http://localhost:8003/health  # IDEALZR
```

## Project Structure

```
CommandCentral/
├── backend/              # CommandCentral service
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── middleware/
│   │   └── schemas/
│   ├── data/
│   ├── requirements.txt
│   └── Dockerfile
├── pipelzr/              # PIPELZR service
│   └── (same structure)
├── vislzr/               # VISLZR service
│   └── (same structure)
├── idealzr/              # IDEALZR service
│   └── (same structure)
├── docker-compose.yml
├── ARCHITECTURE.md
└── README.md
```

## Development

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)

### Environment Variables

Each service has a `.env.example` file. Copy it to `.env` and configure:

```bash
cp backend/.env.example backend/.env
cp pipelzr/.env.example pipelzr/.env
cp vislzr/.env.example vislzr/.env
cp idealzr/.env.example idealzr/.env
```

### Running Tests

```bash
cd backend && pytest
cd pipelzr && pytest
cd vislzr && pytest
cd idealzr && pytest
```

## License

MIT
