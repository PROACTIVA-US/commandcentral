---
name: cleanup-background-tasks
updated: 2026-01-14 11:53
---

# Cleanup Background Tasks

Automatically check for and kill duplicate/unnecessary background processes when starting new dev servers.

## When to Use

- Before starting backend/frontend dev servers
- When switching between projects
- When restarting services after crashes
- When debugging port conflicts

## Process Detection

```bash
# Check for CC4 processes
ps aux | grep -E "(uvicorn|vite)" | grep -v grep | grep CC4

# Check port usage
lsof -i :3001 -i :3002 -i :3003 -i :8001 | grep LISTEN
```

## Cleanup Rules

### Frontend (Vite/npm)
- **Keep**: Most recent vite process (highest PID)
- **Kill**: Older duplicate vite processes
- **Ports**: 3001-3003 (auto-incremented by Vite)

### Backend (uvicorn)
- **Keep**: Most recent uvicorn process on port 8001
- **Kill**: Old/stale uvicorn processes
- **Port**: 8001 (fixed)

## Cleanup Script

```bash
#!/bin/bash
# Kill duplicate vite processes (keep newest)
vite_pids=$(ps aux | grep "CC4.*vite" | grep -v grep | awk '{print $2}' | sort -n)
if [ $(echo "$vite_pids" | wc -l) -gt 1 ]; then
  # Kill all but the last (newest) process
  echo "$vite_pids" | head -n -1 | xargs kill 2>/dev/null
  echo "Killed old Vite processes"
fi

# Kill duplicate uvicorn processes (keep newest)
uvicorn_pids=$(ps aux | grep "CC4.*uvicorn" | grep -v grep | awk '{print $2}' | sort -n)
if [ $(echo "$uvicorn_pids" | wc -l) -gt 1 ]; then
  echo "$uvicorn_pids" | head -n -1 | xargs kill 2>/dev/null
  echo "Killed old uvicorn processes"
fi
```

## Safe Restart Workflow

1. **Check current state**
   ```bash
   ps aux | grep -E "CC4.*(vite|uvicorn)" | grep -v grep
   lsof -i :8001 -i :3001 | grep LISTEN
   ```

2. **Kill duplicates** (use script above)

3. **Start fresh**
   ```bash
   # Backend
   cd backend && source .venv/bin/activate && uvicorn app.main:app --port 8001 &

   # Frontend
   cd frontend && npm run dev &
   ```

4. **Verify**
   ```bash
   # Should show exactly 1 backend + 1 frontend
   ps aux | grep -E "CC4.*(vite|uvicorn)" | grep -v grep | wc -l
   ```

## Integration with Startup

Before running any dev server command:

```bash
# 1. Check for existing processes
existing=$(ps aux | grep -E "CC4.*(vite|uvicorn)" | grep -v grep)

# 2. If found, clean up duplicates
if [ -n "$existing" ]; then
  echo "Found existing processes, cleaning up..."
  # Run cleanup script
fi

# 3. Start new process
```

## Common Issues

### Port Already in Use
- Vite auto-increments: 3001 → 3002 → 3003
- Backend requires manual kill if port 8001 is blocked
- Solution: Kill old process first

### Orphaned Processes
- Caused by: SIGKILL (kill -9), crashes, forced terminal close
- Detection: Process still in `ps` but not responding
- Solution: `kill -9 <PID>` as last resort

### Multiple Projects
- Problem: Other projects (VERIA_PLATFORM) may use same ports
- Solution: Check process path in `ps aux` output includes "CC4"

## Notes

- Always prefer graceful shutdown (SIGTERM) over SIGKILL
- Keep the most recent process (highest PID) to preserve latest code changes
- Vite HMR state is lost when killing processes - requires browser refresh
- Backend state (DB connections) should gracefully close on SIGTERM
