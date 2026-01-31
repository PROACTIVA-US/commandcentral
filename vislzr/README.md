# VISLZR - Visualization & Exploration Service

VISLZR is the visualization and exploration service for the CommandCentral platform. It provides graph visualization, canvas management, and interactive exploration capabilities.

## Features

- **Canvas Management**: Create and manage visualization canvases
- **Node & Relationship CRUD**: Full lifecycle management for graph entities
- **Graph Exploration**: BFS traversal, path finding, and neighbor discovery
- **Wander Mode**: Random walk exploration for serendipitous discovery
- **Cluster Detection**: Find densely connected groups of nodes
- **Multiple Layout Types**: Force-directed, hierarchical, radial, and more

## Quick Start

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Run the service
uvicorn app.main:app --reload --port 8002
```

### Using Docker

```bash
# Build image
docker build -t vislzr .

# Run container
docker run -p 8002:8000 vislzr
```

## API Endpoints

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/ready` | Readiness check |
| GET | `/metrics` | Service metrics |

### Canvases

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/canvases` | Create a canvas |
| GET | `/api/v1/canvases` | List canvases |
| GET | `/api/v1/canvases/{id}` | Get canvas by ID |
| PATCH | `/api/v1/canvases/{id}` | Update canvas |
| DELETE | `/api/v1/canvases/{id}` | Delete canvas |
| POST | `/api/v1/canvases/{id}/nodes` | Add nodes to canvas |
| DELETE | `/api/v1/canvases/{id}/nodes` | Remove nodes from canvas |
| POST | `/api/v1/canvases/{id}/layouts` | Create layout |
| GET | `/api/v1/canvases/{id}/layouts` | List layouts |

### Nodes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/nodes` | Create a node |
| GET | `/api/v1/nodes` | List nodes |
| GET | `/api/v1/nodes/{id}` | Get node by ID |
| PATCH | `/api/v1/nodes/{id}` | Update node |
| DELETE | `/api/v1/nodes/{id}` | Delete node |
| PUT | `/api/v1/nodes/{id}/position` | Update node position |
| POST | `/api/v1/nodes/bulk` | Bulk create nodes |
| POST | `/api/v1/nodes/relationships` | Create relationship |
| GET | `/api/v1/nodes/{id}/relationships` | Get node relationships |
| GET | `/api/v1/nodes/{id}/connected` | Get connected nodes |

### Exploration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/exploration/explore` | Explore graph from node |
| POST | `/api/v1/exploration/path` | Find shortest path |
| POST | `/api/v1/exploration/wander` | Random walk exploration |
| POST | `/api/v1/exploration/clusters` | Find node clusters |
| POST | `/api/v1/exploration/search` | Search nodes |
| GET | `/api/v1/exploration/search` | Search nodes (GET) |
| GET | `/api/v1/exploration/stats/{id}` | Get node statistics |
| GET | `/api/v1/exploration/neighbors/{id}` | Get neighbors |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | VISLZR | Service name |
| `APP_VERSION` | 1.0.0 | Version string |
| `DEBUG` | false | Enable debug mode |
| `HOST` | 0.0.0.0 | Bind host |
| `PORT` | 8000 | Bind port (8002 in docker-compose) |
| `DATABASE_URL` | sqlite+aiosqlite:///./data/vislzr.db | Database connection |
| `SECRET_KEY` | - | JWT secret (must match CommandCentral) |
| `CORS_ORIGINS` | localhost:3000-3002,5173 | Allowed CORS origins |
| `COMMANDCENTRAL_URL` | http://localhost:8000 | CommandCentral service URL |
| `MAX_NODES_PER_CANVAS` | 500 | Maximum nodes per canvas |
| `MAX_DEPTH` | 5 | Maximum exploration depth |

## Architecture

```
vislzr/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings and configuration
│   ├── database.py          # SQLAlchemy async setup
│   ├── middleware/          # Request middleware
│   │   ├── logging.py       # Request/response logging
│   │   ├── correlation.py   # Request correlation IDs
│   │   ├── rate_limit.py    # Token bucket rate limiting
│   │   └── metrics.py       # Request metrics collection
│   ├── models/              # SQLAlchemy models
│   │   ├── node.py          # Node entity
│   │   ├── relationship.py  # Relationship entity
│   │   └── layout.py        # Layout and Canvas entities
│   ├── routers/             # API routers
│   │   ├── health.py        # Health endpoints
│   │   ├── canvas.py        # Canvas management
│   │   ├── nodes.py         # Node/relationship CRUD
│   │   └── exploration.py   # Graph exploration
│   └── services/            # Business logic
│       ├── canvas_service.py
│       ├── node_service.py
│       └── exploration_service.py
├── data/                    # SQLite database storage
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Inter-Service Communication

VISLZR communicates with other CommandCentral services:

- **CommandCentral** (port 8000): Governance and state machine
- **PIPELZR** (port 8001): Pipeline orchestration
- **IDEALZR** (port 8003): Idea generation and refinement

All inter-service calls include correlation IDs for distributed tracing.

## Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload --port 8002

# Run tests
pytest

# Format code
black app/
ruff check app/ --fix

# Type checking
mypy app/
```

## License

MIT License - see LICENSE file for details.
