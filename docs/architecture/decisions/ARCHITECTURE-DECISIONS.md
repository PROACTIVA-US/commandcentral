---
title: Architecture Decisions - Microservices Split
created: 2026-01-31
status: decided
---

# Architecture Decisions - Microservices Split

## Summary

These decisions address the architectural gap exposed when splitting CC4 into 4 microservices and attempting to build CommandCentral's frontend.

## Decision Record

### 1. Skill Ownership

**Decision:** Each service owns its skills; PIPELZR indexes them.

**Rationale:**
- Services know their domain best
- PIPELZR needs a unified view for orchestration
- Skills evolve with their service
- Central registry enables cross-service skill discovery

**Implementation:**
- Each service maintains `/docs/service-spec/skills/` directory
- Each service provides `manifest.json` listing skills
- PIPELZR queries services for skill definitions
- PIPELZR caches skill index for performance

### 2. Knowledge Format

**Decision:** Markdown for human-readable + YAML/JSON for machine-parseable.

**Rationale:**
- Markdown is easy to maintain and review
- Agents need structured data for context
- YAML skills provide clear schema for validation
- JSON manifest enables programmatic access

**Implementation:**
- `/docs/service-spec/*.md` - Human-readable documentation
- `/docs/service-spec/skills/*.yaml` - Machine-readable skill definitions
- `/docs/service-spec/skills/manifest.json` - Skill index

### 3. Execution Location

**Decision:** CC4 short-term; migrate to PIPELZR long-term.

**Rationale:**
- CC4 has working pipeline infrastructure
- PIPELZR is the logical home for execution
- Gradual migration reduces risk
- Both can coexist during transition

**Implementation:**
- Phase 1: CC4 executes with new config format
- Phase 2: PIPELZR gains execution capability
- Phase 3: Migrate execution to PIPELZR
- Phase 4: CC4 pipeline deprecated for cross-repo

### 4. Shared Components

**Decision:** Shared base (shadcn); independent implementations.

**Rationale:**
- Consistent look and feel across services
- Each service has design autonomy
- shadcn components are copy-paste, not npm package
- Reduces coupling between frontends

**Implementation:**
- All services use Tailwind + shadcn/ui
- No shared npm UI package
- Design tokens shared via CSS variables
- Each frontend is independently deployable

---

## Artifacts Created

### Standards (`/docs/standards/`)

| File | Purpose |
|------|---------|
| `service-self-documentation-spec.md` | Defines `/docs/service-spec/` structure |
| `skill-definition-spec.md` | Defines skill YAML schema |
| `pipeline-configuration-spec.md` | Defines pipeline config schema |

### Self-Documentation (`/docs/service-spec/`)

| File | Purpose |
|------|---------|
| `api-reference.md` | All CommandCentral API endpoints |
| `domain-model.md` | Entities, relationships, state machines |
| `patterns.md` | Coding patterns and conventions |
| `dependencies.md` | Runtime and dev dependencies |

### Skills (`/docs/service-spec/skills/`)

| File | Purpose |
|------|---------|
| `manifest.json` | Index of available skills |
| `auth-frontend.yaml` | Authentication UI skill |
| `dashboard-frontend.yaml` | Dashboard page skill |
| `governance-frontend.yaml` | Decisions/audit UI skill |
| `projects-frontend.yaml` | Project management UI skill |

### Architecture (`/docs/architecture/`)

| File | Purpose |
|------|---------|
| `CRITICAL-microservices-split-issue.md` | Problem statement |
| `ARCHITECTURE-DECISIONS.md` | This file |
| `pipelzr-enhancement-plan.md` | PIPELZR upgrade plan |

---

---

## AI Arena Placement

**Decision:** AI Arena will be located in **CommandCentral UI**.

**Rationale:**
- CommandCentral is the governance/coordination layer
- AI Arena is used for multi-model deliberation on decisions
- Fits naturally with CommandCentral's decision-making responsibility
- Arena sessions can be linked to Decisions, Projects, etc.

**Implementation Notes:**
- AI Arena backend currently in CC4 at `/backend/app/services/arena_service.py`
- Must be migrated to CommandCentral backend
- Frontend components needed in CommandCentral `/frontend/src/features/arena/`
- Session data should link to `project_id` for context

**Supported Providers (as of 2026-01-31):**
- Anthropic (Claude)
- OpenAI (GPT-5.2, etc.)
- Google Gemini
- xAI (Grok)
- Z.ai (GLM)
- Moonshot AI (Kimi 2.5) - newly added

---

## Next Steps

1. **Review documents** - Validate decisions and standards
2. **Implement PIPELZR enhancements** - Follow enhancement plan
3. **Test with CommandCentral** - Build frontend with new system
4. **Document learnings** - Update standards based on results
5. **Replicate for other services** - Create self-docs for PIPELZR, VISLZR, IDEALZR
6. **Migrate AI Arena** - Move arena service to CommandCentral

---

## Success Metrics

- [ ] CommandCentral frontend builds successfully
- [ ] Generated code matches spec requirements
- [ ] No context bleed from CC4 patterns
- [ ] Validation checks pass
- [ ] Agents use correct domain knowledge
