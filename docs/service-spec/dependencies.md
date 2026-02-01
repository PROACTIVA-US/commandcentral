---
title: CommandCentral Dependencies
version: 1.0.0
updated: 2026-01-31
service: commandcentral
---

# CommandCentral Dependencies

## Backend Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | ^0.109.0 | Web framework |
| uvicorn | ^0.27.0 | ASGI server |
| sqlalchemy | ^2.0.25 | ORM |
| aiosqlite | ^0.19.0 | Async SQLite driver |
| pydantic | ^2.5.0 | Data validation |
| pydantic-settings | ^2.1.0 | Settings management |
| python-jose | ^3.3.0 | JWT handling |
| passlib | ^1.7.4 | Password hashing |
| bcrypt | ^4.1.2 | Password hashing backend |
| python-multipart | ^0.0.6 | Form data handling |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | ^7.4.0 | Testing framework |
| pytest-asyncio | ^0.23.0 | Async test support |
| httpx | ^0.26.0 | Async HTTP client for tests |
| ruff | ^0.1.0 | Linting |
| mypy | ^1.8.0 | Type checking |
| black | ^23.12.0 | Code formatting |
| alembic | ^1.13.0 | Database migrations |

### requirements.txt

```
# Core
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.25
aiosqlite>=0.19.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
```

### requirements-dev.txt

```
-r requirements.txt

# Testing
pytest>=7.4.0
pytest-asyncio>=0.23.0
httpx>=0.26.0

# Quality
ruff>=0.1.0
mypy>=1.8.0
black>=23.12.0

# Database
alembic>=1.13.0
```

---

## Frontend Dependencies (Planned)

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| react | ^18.2.0 | UI framework |
| react-dom | ^18.2.0 | DOM rendering |
| react-router-dom | ^6.21.0 | Routing |
| @tanstack/react-query | ^5.17.0 | Data fetching |
| zustand | ^4.4.7 | State management |
| axios | ^1.6.5 | HTTP client |
| zod | ^3.22.4 | Schema validation |
| react-hook-form | ^7.49.0 | Form handling |
| @hookform/resolvers | ^3.3.4 | Form validation |
| lucide-react | ^0.309.0 | Icons |
| date-fns | ^3.2.0 | Date utilities |
| clsx | ^2.1.0 | Class names |
| tailwind-merge | ^2.2.0 | Tailwind utilities |

### UI Components (shadcn/ui)

```
button
card
input
dialog
tabs
dropdown-menu
toast
select
checkbox
avatar
badge
progress
skeleton
separator
scroll-area
command
popover
form
label
textarea
```

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| typescript | ^5.3.3 | Type system |
| vite | ^5.0.11 | Build tool |
| @vitejs/plugin-react | ^4.2.1 | React plugin |
| tailwindcss | ^3.4.1 | CSS framework |
| postcss | ^8.4.33 | CSS processing |
| autoprefixer | ^10.4.16 | CSS prefixing |
| eslint | ^8.56.0 | Linting |
| eslint-plugin-react | ^7.33.2 | React linting |
| @types/react | ^18.2.48 | React types |
| @types/react-dom | ^18.2.18 | DOM types |

### package.json (Planned)

```json
{
  "name": "commandcentral-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "@tanstack/react-query": "^5.17.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.5",
    "zod": "^3.22.4",
    "react-hook-form": "^7.49.0",
    "@hookform/resolvers": "^3.3.4",
    "lucide-react": "^0.309.0",
    "date-fns": "^3.2.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",
    "class-variance-authority": "^0.7.0",
    "@radix-ui/react-slot": "^1.0.2",
    "sonner": "^1.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.33",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.11",
    "vitest": "^1.2.0"
  }
}
```

---

## External Service Dependencies

| Service | Required | Purpose |
|---------|----------|---------|
| PIPELZR (8001) | Optional | Task execution, pipelines |
| VISLZR (8002) | Optional | Canvas visualization |
| IDEALZR (8003) | Optional | Goals, hypotheses |

CommandCentral can operate independently, but full functionality requires other services.

---

## Environment Variables

### Required

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./commandcentral.db` | Database connection |
| `SECRET_KEY` | - | JWT signing key (REQUIRED in production) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiration |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed origins |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PIPELZR_URL` | `http://localhost:8001` | PIPELZR service URL |
| `VISLZR_URL` | `http://localhost:8002` | VISLZR service URL |
| `IDEALZR_URL` | `http://localhost:8003` | IDEALZR service URL |

### .env.example

```bash
# Required
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite+aiosqlite:///./commandcentral.db

# JWT
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional
DEBUG=true
CORS_ORIGINS=["http://localhost:3000","http://localhost:3002"]
LOG_LEVEL=DEBUG

# External Services
PIPELZR_URL=http://localhost:8001
VISLZR_URL=http://localhost:8002
IDEALZR_URL=http://localhost:8003
```

---

## System Requirements

### Backend

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ |
| pip | 23.0+ |

### Frontend

| Requirement | Version |
|-------------|---------|
| Node.js | 20+ |
| npm | 10+ |

### Database

| Database | Notes |
|----------|-------|
| SQLite | Default, file-based |
| PostgreSQL | Recommended for production |
