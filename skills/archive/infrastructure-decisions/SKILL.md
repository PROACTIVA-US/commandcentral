---
name: infrastructure-decisions
description: Guidelines for choosing between infrastructure approaches (Dagger vs YAML, programmatic vs declarative). Use during design phases when containerization, CI/CD, or orchestration decisions are needed.
---

# Infrastructure Decision Guidelines

Choose the right tool for infrastructure needs.

## Decision Matrix

Use this matrix to evaluate your infrastructure needs and choose the appropriate approach:

| Criteria | Docker Compose | Dagger | Weight |
|----------|---------------|--------|--------|
| **Complexity** | Simple services | Complex builds/orchestration | High |
| **Customization** | Standard images | Custom images + extensions | High |
| **Testing Needs** | Single environment | Multi-environment matrices | High |
| **Team Skills** | Widely known | Requires Python/Go knowledge | Medium |
| **CI/CD Integration** | Limited | Excellent | High |
| **Programmatic Control** | No | Yes (start/stop via code) | Medium |
| **Configuration** | Static YAML | Dynamic at runtime | Medium |
| **Reproducibility** | Environment-dependent | Guaranteed across envs | High |
| **Local Development** | Excellent | Good | Low |
| **Learning Curve** | Low | Medium | Low |

**Scoring Guide:**
- 3+ "Dagger" advantages (High weight) → **Use Dagger**
- 2+ "Compose" advantages (High weight) → **Use Docker Compose**
- Mixed results → Start with Compose, migrate to Dagger when needed

## Enhanced Decision Flowchart

```
┌─────────────────────────────────────────────┐
│ Infrastructure Decision Flowchart           │
└─────────────────────────────────────────────┘

START: What infrastructure do you need?
   │
   ├─→ Need custom Docker image with extensions?
   │   (e.g., Postgres + pgvector + ParadeDB)
   │   YES → ✅ DAGGER
   │   NO ↓
   │
   ├─→ Need to test against multiple backends/versions?
   │   (e.g., ChromaDB vs Postgres vs Qdrant)
   │   YES → ✅ DAGGER
   │   NO ↓
   │
   ├─→ Need programmatic orchestration?
   │   (start/stop services via code, dynamic scaling)
   │   YES → ✅ DAGGER
   │   NO ↓
   │
   ├─→ Need CI/CD pipeline reproducibility?
   │   (same exact build local and remote)
   │   YES → ✅ DAGGER
   │   NO ↓
   │
   ├─→ Configuration determined at runtime?
   │   (parameters from env vars, API calls, etc.)
   │   YES → ✅ DAGGER
   │   NO ↓
   │
   └─→ Just need services running for local dev?
       (standard images, static config)
       → ✅ DOCKER COMPOSE

Special Cases:
├─ Building production images → DAGGER (for CI/CD)
├─ Microservices with 10+ services → DOCKER COMPOSE (simplicity)
└─ Hybrid: Compose for local dev + Dagger for tests/CI
```

## Real-World Examples

### Example 1: KnowledgeBeast Vector Database Testing

**Scenario:** Need to test application against multiple vector database backends (ChromaDB, Postgres with pgvector, Qdrant) to ensure compatibility.

**Decision:** ✅ **Dagger**

**Why:**
- Testing matrix requirement (3 different backends)
- Custom Postgres image needed (pgvector extension)
- Tests run in CI/CD - need reproducibility
- Programmatic control to start/stop different backends

**Implementation:**
```python
# tests/conftest.py
import dagger
import pytest

@pytest.fixture(params=["chromadb", "postgres", "qdrant"])
async def vector_db(request):
    async with dagger.Connection() as client:
        if request.param == "postgres":
            db = (
                client.container()
                .from_("postgres:16")
                .with_exec(["apt-get", "update"])
                .with_exec(["apt-get", "install", "-y", "postgresql-16-pgvector"])
                .with_env_variable("POSTGRES_PASSWORD", "test")
                .with_exposed_port(5432)
            ).as_service()
        elif request.param == "chromadb":
            db = (
                client.container()
                .from_("chromadb/chroma:latest")
                .with_exposed_port(8000)
            ).as_service()
        # ... qdrant implementation
        yield db
```

**Outcome:** All tests run against all backends automatically, catching compatibility issues early.

---

### Example 2: Simple Web App Development

**Scenario:** Developer needs Postgres, Redis, and RabbitMQ running locally to develop a web application.

**Decision:** ✅ **Docker Compose**

**Why:**
- Standard, unmodified images
- Static configuration (same ports, passwords every time)
- Team already familiar with docker-compose
- No testing matrix needed
- Just needs services running

**Implementation:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: devpassword
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
```

**Outcome:** Developers run `docker-compose up` and start coding immediately.

---

### Example 3: CommandCenter Hub Orchestration

**Scenario:** CommandCenter Hub needs to programmatically spin up multiple CommandCenter instances, each with isolated environments.

**Decision:** ✅ **Dagger**

**Why:**
- Programmatic orchestration (create instances on-demand)
- Dynamic configuration (each instance gets unique ports, env vars)
- Complex multi-container orchestration
- Needs to start/stop instances via API calls
- CI/CD integration for testing the hub itself

**Implementation:**
```python
# hub/orchestrator.py
import dagger

class CommandCenterHub:
    async def create_instance(self, instance_id: str, config: dict):
        async with dagger.Connection() as client:
            # Build custom CC instance with specific config
            instance = (
                client.container()
                .from_("commandcenter:latest")
                .with_env_variable("INSTANCE_ID", instance_id)
                .with_env_variable("CONFIG", json.dumps(config))
                .with_exposed_port(config["port"])
            ).as_service()
            
            self.instances[instance_id] = instance
            return instance
    
    async def stop_instance(self, instance_id: str):
        # Programmatic control - stop specific instance
        await self.instances[instance_id].stop()
```

**Outcome:** Hub can dynamically manage CC instances based on demand.

---

### Example 4: CI/CD Pipeline for Microservices

**Scenario:** Need to build, test, and deploy 5 microservices with consistent environments across developer machines and GitHub Actions.

**Decision:** ✅ **Dagger**

**Why:**
- CI/CD reproducibility critical (works locally = works in CI)
- Multiple services need coordinated builds
- Custom build steps for each service
- Same pipeline should work on any machine

**Implementation:**
```python
# ci/pipeline.py
import dagger

async def build_and_test():
    async with dagger.Connection() as client:
        # Build all services
        services = {}
        for svc in ["auth", "api", "worker", "scheduler", "web"]:
            services[svc] = (
                client.container()
                .from_("python:3.11")
                .with_directory(f"/app", client.host().directory(f"./services/{svc}"))
                .with_workdir("/app")
                .with_exec(["pip", "install", "-r", "requirements.txt"])
                .with_exec(["pytest"])
            )
        
        # Run integration tests with all services
        # ... integration test logic
```

**Outcome:** `python ci/pipeline.py` works identically on laptops and CI runners.

---

### Example 5: Postgres with Custom Extensions (ParadeDB + pgvector)

**Scenario:** Application needs Postgres with both ParadeDB (full-text search) and pgvector (embeddings) extensions installed.

**Decision:** ✅ **Dagger**

**Why:**
- No official Docker image with both extensions
- Custom build process required
- Needs to work in both dev and CI
- Complex installation steps

**Implementation:**
```python
# infra/database.py
import dagger

async def create_custom_postgres():
    async with dagger.Connection() as client:
        postgres = (
            client.container()
            .from_("postgres:16")
            
            # Install pgvector
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "postgresql-16-pgvector"])
            
            # Install ParadeDB
            .with_exec(["apt-get", "install", "-y", "curl", "gnupg"])
            .with_exec([
                "sh", "-c",
                "curl -fsSL https://github.com/paradedb/paradedb/releases/download/v0.5.0/paradedb.deb -o paradedb.deb"
            ])
            .with_exec(["dpkg", "-i", "paradedb.deb"])
            
            # Configure
            .with_env_variable("POSTGRES_PASSWORD", "secret")
            .with_exposed_port(5432)
        ).as_service()
        
        return postgres
```

**Outcome:** Complex custom database available consistently everywhere.

---

## Dagger vs Docker Compose

### Use Dagger When:

- **Custom images with extensions** (Postgres + pgvector + ParadeDB)
- **Testing matrices** (test against multiple backends/versions)
- **Programmatic orchestration** (start/stop services via code)
- **Dynamic configuration** (parameters determined at runtime)
- **CI/CD pipelines** (reproducible builds across environments)

### Use docker-compose.yml When:

- **Static service definitions** (standard images, fixed config)
- **Simple local development** (just need services running)
- **No customization needed** (vanilla Postgres, Redis, etc.)
- **Team familiarity** (everyone knows compose)

## Dagger Quick Reference

```python
# Basic pattern
import dagger

async with dagger.Connection() as client:
    postgres = (
        client.container()
        .from_("postgres:16")
        .with_env_variable("POSTGRES_PASSWORD", "secret")
        .with_exposed_port(5432)
    )
    service = postgres.as_service()
```

**Key patterns:**
- `container().from_()` - Base image
- `.with_exec()` - Run commands (for custom builds)
- `.with_env_variable()` - Set env vars
- `.as_service()` - Convert to running service
- Order operations from least-changing to most-changing (caching)

## Project Examples

| Project | Approach | Reason |
|---------|----------|--------|
| CommandCenter Hub | Dagger | Orchestrates multiple CC instances programmatically |
| KnowledgeBeast tests | Dagger | Test matrix: ChromaDB vs Postgres backends |
| Local dev environment | Compose | Just need Postgres + Redis running |
| CI/CD pipeline | Dagger | Reproducible across local/CI |

## Hybrid Approach

Sometimes the best solution is **both**:

```
Local Development: docker-compose.yml
    ├─ Fast startup
    ├─ Simple for daily work
    └─ Standard services only

Testing & CI: Dagger
    ├─ Custom images for tests
    ├─ Matrix testing
    └─ Reproducible builds
```

**Example structure:**
```
project/
├─ docker-compose.yml          # Local dev: Postgres, Redis
├─ tests/
│  └─ dagger_config.py         # Tests: Custom Postgres + matrix
└─ ci/
   └─ pipeline.py              # CI: Dagger-based builds
```

## References

For detailed Dagger implementation patterns, see:
- `docs/UNIVERSAL_DAGGER_PATTERN.md` in CommandCenter
- Dagger docs: https://docs.dagger.io/
