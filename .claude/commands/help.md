When the user types /help, display this information:

# CommandCentral Workflow

## Session Management

| Command | Use When |
|---------|----------|
| `claude` | Start fresh session |
| `claude --continue` | Continue today's work |
| `claude --resume` | Pick from recent sessions |
| `/clear` | **Use frequently** between distinct tasks |

## Slash Commands

| Command | Purpose |
|---------|---------|
| `/help` | This guide |
| `/review` | Get workflow improvement suggestions |
| `/plan [topic]` | Create a structured work plan |

## Recommended Workflow

```
Explore -> Plan -> Implement -> Commit -> Clear
```

## Key Commands

```bash
# Run all services
docker-compose up -d

# Run single service
cd backend && uvicorn app.main:app --port 8000 --reload

# Test
cd backend && pytest
```

## Tips

- Be specific upfront to reduce back-and-forth
- Commit after each successful change
- Use `/clear` between unrelated tasks
