---
status: active
name: model-governance
description: MANDATORY - Always use latest model versions. Never use outdated models.
priority: P0
enforcement: blocking
updated: 2026-02-02 20:20
contract:
  version: '1.0'
  inputs:
    required:
    - name: model_selection
      type: string
      description: Model being used for any AI task
  outputs:
  - name: validation
    type: object
    properties:
      valid:
        type: boolean
      model:
        type: string
  errors:
  - code: OUTDATED_MODEL
    description: Using an outdated model version
    recoverable: true
---
# Model Governance

**MANDATORY P0 SKILL - ALWAYS USE LATEST MODELS**

## Essence (50 words)

NEVER use outdated models. Gemini: `gemini-2.5-flash-preview-05-20`. Claude: `claude-opus-4-5-20251101` or `claude-sonnet-4-20250514`. Check this skill BEFORE any pipeline or agent configuration. Outdated models = BLOCKED. This is non-negotiable.

---

## Current Latest Models (2026-02)

### Google Gemini
| Use Case | Model ID | Notes |
|----------|----------|-------|
| **Agentic Vision** | `gemini-3.0-flash-preview` | Code execution, multimodal, REQUIRED for vision pipelines |
| **Fast Tasks** | `gemini-2.5-flash-preview-05-20` | Standard tasks |
| **Pro Tasks** | `gemini-2.5-pro-preview-05-06` | Complex reasoning |

**CRITICAL**: Agentic Vision (code_execution tool) ONLY works with Gemini 3 Flash.

### Anthropic Claude
| Use Case | Model ID | Notes |
|----------|----------|-------|
| **Best Quality** | `claude-opus-4-5-20251101` | Frontier model |
| **Balanced** | `claude-sonnet-4-20250514` | Fast + capable |

---

## Deprecated Models (DO NOT USE)

These models are **BLOCKED** - using them is a skill violation:

```
# BLOCKED Gemini Models
gemini-2.0-flash          # Outdated - no agentic vision
gemini-pro                # Outdated
gemini-1.5-pro            # Outdated
gemini-1.5-flash          # Outdated

# BLOCKED Claude Models
claude-3-opus             # Outdated
claude-3-sonnet           # Outdated
claude-3-haiku            # Outdated
claude-2                  # Outdated
```

---

## Enforcement Rules

### P0 Blocking Conditions
1. **Pipeline YAML**: Any `model:` field MUST use latest versions
2. **Agent Config**: Any model selection MUST use latest versions
3. **API Calls**: Any direct API calls MUST use latest versions

### Validation Checks
```yaml
# CORRECT
config:
  model: gemini-2.5-flash-preview-05-20

# WRONG - BLOCKED
config:
  model: gemini-2.0-flash  # OUTDATED
```

---

## Why This Matters

1. **Capability Gap**: Older models lack critical features (code execution, vision)
2. **API Changes**: Older model APIs may have different request formats
3. **Quality**: Latest models have significantly better performance
4. **Consistency**: All pipelines should use the same model versions

---

## Update Protocol

When new models are released:
1. Update this skill's "Current Latest Models" section
2. Move old versions to "Deprecated Models"
3. Update all pipeline YAML files
4. Update all agent configurations
5. Test with new versions before deployment

---

## Quick Reference

Copy-paste ready model IDs:

```bash
# Gemini 3 Flash - REQUIRED for Agentic Vision (code execution)
export GEMINI_VISION="gemini-3.0-flash-preview"

# Gemini 2.5 Flash - Standard tasks
export GEMINI_MODEL="gemini-2.5-flash-preview-05-20"

# Claude (use for complex reasoning, code review)
export CLAUDE_MODEL="claude-opus-4-5-20251101"
export CLAUDE_FAST="claude-sonnet-4-20250514"
```

---

*Last updated: 2026-02-02 - Gemini 3 Flash (Agentic Vision), Claude Opus 4.5*
