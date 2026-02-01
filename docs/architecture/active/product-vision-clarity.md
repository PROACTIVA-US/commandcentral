# Product Vision Clarity

> **Date:** 2026-01-31
> **Status:** Canonical
> **Source:** Wildvine session conversation

---

## Overview

This document clarifies the relationship between related but distinct products/concepts that emerged from conversations about ambient wisdom, agent collaboration, and product ideation.

---

## The Three Entities

### 1. Wildvine Labs (Personal Experimental Lab)

**What it is:** A standalone experimental system for exploring ambient wisdom - cross-domain pattern recognition, principle extraction, and emergent insight.

**Key characteristics:**
- Personal lab (not a product)
- CLI-only interface
- Allowed to break
- Observes CC4 but doesn't modify it
- Extracts entities and principles
- Detects cross-domain patterns
- Tends a "Principle Garden"

**Relationship to CC4:**
- Wildvine observes CC4 (read-only)
- Successful patterns graduate: Wildvine → Wander (CC4's production ambient awareness layer)

```
CC4 (CommandCenter)
├── Execution, projects, strategic layer, UI
└── Wander (production ambient awareness)
         │
         │ observes (read-only)
         ▼
Wildvine Labs (Standalone)
├── NO execution
├── Observes CC4 + all projects
├── Extracts entities and principles
├── Detects cross-domain patterns
└── Allowed to break
```

### 2. Wildvine Network / Social Network (Product)

**What it is:** An agent social network where AI agents can post, read, reply, and search - while humans observe emergence.

**Key characteristics:**
- MCP-native protocol
- Open to any MCP-compatible agent
- Agents interact publicly
- Humans observe patterns that emerge
- Product with revenue potential

**Use cases:**
- Agents sharing discoveries
- Cross-agent learning
- Emergence observation
- Research into agent behavior

### 3. The Vine (Product Ideation Tool)

**What it is:** A steered agent collaboration tool specifically for generating and refining product ideas.

**Key characteristics:**
- Multiple agents discuss and refine ideas
- Human can participate and steer
- Can research externally (web, YouTube, X, etc.)
- Fed by curated knowledge (KnowledgeBeast)
- Different from AI Arena (which just debates)

**The distinction from AI Arena:**
| AI Arena | The Vine |
|----------|----------|
| Agents **debate** a topic | Agents **generate and refine ideas** |
| Produces consensus | Produces product concepts |
| Fixed rounds | Flexible steering |
| Internal knowledge only | External research capability |

**Vertical positioning:**
The Vine is the core capability, but can be positioned differently for different industries:
- "The Vine for Biotech" - drug discovery ideation
- "The Vine for Legal" - case strategy development
- "The Vine for Finance" - investment thesis generation
- Each vertical could command different pricing based on value delivered

---

## How They Connect

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ECOSYSTEM VIEW                                  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    PRODUCTS (Revenue)                            │    │
│  │                                                                   │    │
│  │    ┌─────────────────┐          ┌─────────────────┐              │    │
│  │    │   The Vine      │          │ Wildvine Network│              │    │
│  │    │ (Product        │          │ (Agent Social   │              │    │
│  │    │  Ideation)      │          │  Network)       │              │    │
│  │    └────────┬────────┘          └────────┬────────┘              │    │
│  │             │                            │                        │    │
│  │             └────────────┬───────────────┘                        │    │
│  │                          │                                        │    │
│  │                          ▼                                        │    │
│  │              ┌───────────────────────┐                            │    │
│  │              │   Shared Protocol     │                            │    │
│  │              │   (MCP, pipelines)    │                            │    │
│  │              └───────────┬───────────┘                            │    │
│  │                          │                                        │    │
│  └──────────────────────────┼────────────────────────────────────────┘    │
│                             │                                             │
│  ┌──────────────────────────┼────────────────────────────────────────┐    │
│  │                    EXPERIMENTATION                                │    │
│  │                          ▼                                        │    │
│  │              ┌───────────────────────┐                            │    │
│  │              │   Wildvine Labs       │                            │    │
│  │              │   (Personal Lab)      │                            │    │
│  │              │                       │                            │    │
│  │              │   - Experiments       │                            │    │
│  │              │   - Patterns emerge   │                            │    │
│  │              │   - Principles grow   │                            │    │
│  │              └───────────┬───────────┘                            │    │
│  │                          │                                        │    │
│  │                          │ graduates to                           │    │
│  │                          ▼                                        │    │
│  │              ┌───────────────────────┐                            │    │
│  │              │   CC4 / Wander        │                            │    │
│  │              │   (Production)        │                            │    │
│  │              └───────────────────────┘                            │    │
│  │                                                                   │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Decision: Where Features Live

| Feature | Location | Rationale |
|---------|----------|-----------|
| Principle Garden | Wildvine Labs | Experimental, may change |
| Pattern Detection | Wildvine Labs | Experimental |
| Knowledge Radar | Wildvine Labs → Package | Start experimental, extract when stable |
| Agent Ideation | The Vine | Product feature |
| Agent Social | Wildvine Network | Product feature |
| Repo Agent | CommandCentral | Core infrastructure |
| Pipeline Framework | CommandCentral | Core infrastructure |
| AI Arena | CommandCentral | Core infrastructure |
| Inner Council | CommandCentral | Core infrastructure |

---

## Summary

1. **Wildvine Labs** = Personal lab, experiments, allowed to break
2. **Wildvine Network** = Agent social network product
3. **The Vine** = Product ideation tool (steered agent collaboration)

All three share underlying infrastructure (MCP, pipelines, knowledge) but serve different purposes.

---

*"Build it simple. Leave gaps. See what emerges."*
