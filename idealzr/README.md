# IDEALZR - Ideas & Strategic Intelligence Service

IDEALZR is the strategic intelligence hub of the CommandCentral platform, handling goals, hypotheses, evidence, forecasting, venture studio, and knowledge management with provenance tracking.

## Port: 8003 (in docker-compose)

## Features

### Goals Hierarchy
- Hierarchical goal trees with parent-child relationships
- State machine: draft -> active -> achieved/abandoned
- Progress tracking with automatic parent rollup
- Timeline and priority management

### Hypotheses Lifecycle
- Testable assumptions with falsifiability criteria
- State machine: proposed -> investigating -> validated/refuted
- Confidence tracking with history
- Links to goals, ventures, and evidence

### Evidence Collection
- Multiple evidence types (data, research, interview, experiment, etc.)
- Evidence strength ratings (weak, moderate, strong, definitive)
- Automatic hypothesis confidence updates
- Source provenance tracking

### Forecasting & Predictions
- Prediction tracking with resolution dates
- Confidence calibration
- Accuracy metrics by confidence band
- Links to hypotheses and goals

### Venture Studio
- Stage-gated venture development
- Stages: ideation -> validation -> MVP -> pilot -> growth -> mature
- Key metrics tracking
- Team and financial management

### Ideas Capture
- Quick idea capture
- ICE scoring (Impact, Confidence, Ease)
- Promotion to hypothesis/venture/goal
- Status workflow: captured -> reviewing -> promoted/parked/rejected

### Memory & Claims
- Knowledge storage with provenance
- Semantic search capabilities (with embeddings)
- Claim extraction and verification
- Staleness tracking

## Quick Start

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run the server
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/health` | Health check |
| `/metrics` | Service metrics |
| `/api/v1/goals` | Goals CRUD and hierarchy |
| `/api/v1/hypotheses` | Hypothesis lifecycle |
| `/api/v1/evidence` | Evidence collection |
| `/api/v1/forecasts` | Predictions and forecasting |
| `/api/v1/ventures` | Venture studio |
| `/api/v1/ideas` | Quick idea capture |
| `/api/v1/memory` | Memory and claims |

## Documentation

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI: http://localhost:8000/openapi.json

## Architecture

IDEALZR is part of the CommandCentral platform:

```
┌─────────────────────────────────────────────────────────┐
│                    CommandCentral                        │
│              (Governance & Truth State)                  │
│                     Port 8000                            │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   PIPELZR   │      │   VISLZR    │      │   IDEALZR   │
│  Pipelines  │      │   Canvas    │      │ Intelligence│
│  Port 8001  │      │  Port 8002  │      │  Port 8003  │
└─────────────┘      └─────────────┘      └─────────────┘
```

## Models

### Goal
- Hierarchical objectives with progress tracking
- States: draft, active, on_hold, achieved, abandoned

### Hypothesis
- Testable assumptions with confidence tracking
- States: proposed, investigating, validated, refuted, paused, abandoned

### Evidence
- Supporting/contradicting data for hypotheses
- Types: data, research, interview, experiment, observation, document, expert, anecdote
- Strengths: weak, moderate, strong, definitive

### Venture
- Business initiatives in the venture studio
- Stages: ideation, validation, mvp, pilot, growth, mature, sunset, killed

### Idea
- Quick captures before they become hypotheses/ventures
- Statuses: captured, reviewing, promoted, parked, rejected

### Memory & Claim
- Knowledge with source provenance
- Verification and staleness tracking

## Development

```bash
# Run tests
pytest

# Format code
black app/
ruff --fix app/

# Run with debug logging
DEBUG=true uvicorn app.main:app --reload
```

## Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret (must match CommandCentral)
- `COMMANDCENTRAL_URL`: URL to CommandCentral service
- `DEBUG`: Enable debug mode
