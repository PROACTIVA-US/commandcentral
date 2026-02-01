---
name: frontend-composability
description: Guidelines for building composable, maintainable React components. Use before any frontend work.
---

# Frontend Composability

## When to Use

- Before building any new component
- When refactoring existing components
- When reviewing frontend PRs

## Quick Reference

### The 7 Principles

1. **Single Responsibility** - One component, one job
2. **Prop-Driven** - Data via props, not stores (except containers)
3. **Composition Over Configuration** - Small composable parts > big configurable blobs
4. **Container/Presentational Split** - Containers fetch, presentational renders
5. **Reusable Primitives** - Extract common patterns to `ui/`
6. **Explicit Dependencies** - Use `Pick<>` to take only what's needed
7. **Colocation** - Keep related code together

### File Structure

```
components/
├── ui/                    ← Shared primitives
├── [Feature]/
│   ├── index.tsx          ← Container (data fetching)
│   ├── [Component].tsx    ← Presentational
│   ├── hooks/             ← Feature-specific hooks
│   └── modals/            ← Feature-specific modals
```

### Component Size Limits

| Lines | Action |
|-------|--------|
| < 100 | ✅ Good |
| 100-150 | ⚠️ Consider splitting |
| > 150 | ❌ Must split |

### Checklist

Before merging:
- [ ] Single responsibility
- [ ] Props-only (unless container)
- [ ] Under 150 lines
- [ ] Typed interface
- [ ] No inline definitions
- [ ] Testable with mock props

## Full Documentation

See `docs/architecture/frontend-composability.md` for:
- Detailed explanations
- Anti-patterns to avoid
- Current violations audit
- Migration path
