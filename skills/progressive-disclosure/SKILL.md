---
status: active
name: progressive-disclosure
description: Enforces infinite composability through progressive disclosure - every
  UI is a drill-down starting point. Based on VISLZR's Wander pattern.
contract:
  version: '1.0'
  inputs:
    required:
    - name: task_description
      type: string
      description: Description of the task to perform
    optional: []
  outputs:
  - name: result
    type: object
    properties:
      success:
        type: boolean
      summary:
        type: string
  errors:
  - code: SKILL_EXECUTION_FAILED
    description: Skill execution encountered an error
    recoverable: true
  side_effects:
  - type: api_call
    description: May call external APIs
  - type: database_write
    description: May modify database
  auth_scopes: []
  timeouts:
    default_ms: 30000
    max_ms: 180000
---
# Progressive Disclosure & Infinite Composability

> **Core Principle**: Every view is a summary. Every element is clickable. Every click reveals deeper context while preserving parent context.

This skill captures the VISLZR Wander navigation pattern as a universal UI architecture requirement.

---

## 🚨 REQUIRED DECLARATIONS (Pipeline Rules)

**Before ANY UI task can proceed to code generation, you MUST specify:**

### 1. Summary View Spec
What information shows at first glance (the "collapsed" state)?

```markdown
## Summary View
- What: [Primary identifier/title]
- Key metrics: [2-3 most important numbers]
- Status indicator: [Current state]
- Quick action: [Most common next step]
```

### 2. Detail View Spec  
What information shows when expanded/clicked?

```markdown
## Detail View
- Full entity data
- Related entities (children)
- History/timeline
- Available actions
```

### 3. Click Behavior Spec
How does drilling down work?

| Click Target | Behavior | Context Preserved |
|--------------|----------|-------------------|
| Card/Row | Expand in place / Side panel / Navigate | Yes / Partial / No |
| Nested entity | Same options | Parent visible? |
| Action button | Modal / Inline / Navigate | State preserved? |

### 4. Parent Context Spec
What stays visible during drill-down?

```markdown
## Context Preservation
- Breadcrumb: [Parent > Current > Child]
- Side panel: Parent stays visible
- Header: Shows parent context summary
```

### 5. Child Entities Spec
What can the user drill into from this view?

```markdown
## Drill-Down Targets
- [Entity A] → leads to [Detail A]
- [Entity B] → leads to [Detail B]
- [Metric] → leads to [Breakdown]
```

---

## 📐 The Pattern: VISLZR Wander Navigation

The canonical example is VISLZR's Wander mode:

```
User clicks node
    ↓
Graph reorients (300ms animation)
    ├─ Parent nodes move above
    ├─ Clicked node becomes center
    ├─ Child nodes appear below
    └─ Breadcrumb trail updates
    ↓
User sees new context
    ├─ Sibling action nodes appear (contextual)
    └─ Can drill deeper or navigate up
```

**Key Properties:**
1. **On-demand generation** - Children aren't pre-loaded, generated when needed
2. **Context preservation** - Breadcrumb shows path, can navigate back
3. **Infinite depth** - Any node can have children, no arbitrary limits
4. **Consistent interaction** - Click always means "show me more"

---

## 🏠 PropertyManager Example

The PropertyManager vision demonstrates this pattern in a business app:

### Owner Dashboard (Summary View)
```
┌─────────────────────────────────────────┐
│ 123 Main Street                    [$$$]│  ← Property clickable
│ Current Value: $450,000  Equity: $180k  │  ← Values clickable
│ Status: Occupied                        │
│ Tenant: John Smith ────────────────────→│  ← Tenant clickable
│                                         │
│ Utilities  Documents  Maintenance       │  ← Each clickable
└─────────────────────────────────────────┘
```

### After clicking "Utilities" (Detail View)
```
┌─ 123 Main Street > Utilities ───────────┐  ← Breadcrumb
│                                         │
│ ⚡ Electric   $142/mo   ───────────────→│  ← Provider clickable
│ 💧 Water      $45/mo    ───────────────→│
│ 🔥 Gas        $78/mo    ───────────────→│
│                                         │
│ Total: $265/mo                          │
└─────────────────────────────────────────┘
```

### After clicking "Electric" (Deeper Detail)
```
┌─ 123 Main St > Utilities > Electric ────┐
│                                         │
│ Provider: PG&E                          │
│ Account: ****4521                        │
│ Avg: $142/mo                            │
│                                         │
│ [View Bills] [View Usage] [Contact]     │
│                                         │
│ Recent:                                 │
│   Jan 2026: $156  ─────────────────────→│  ← Bill clickable
│   Dec 2025: $134  ─────────────────────→│
└─────────────────────────────────────────┘
```

**The pattern continues infinitely:**
- Bill → Payment details, PDF, dispute options
- Provider → All properties with this provider, contact info
- Usage → Charts, comparisons, recommendations

---

## ✅ Validation Rules

### P0: Blocking (Must Pass)

1. **No Dead Ends**
   - Every view must have at least one drill-down option
   - ❌ Page with only static text
   - ✅ Every entity/metric clickable to more detail

2. **Context Always Preserved**
   - User must always know where they are
   - ❌ Modal opens with no indication of parent
   - ✅ Breadcrumb/header shows navigation path

3. **Consistent Click Semantics**
   - Click = "show me more about this"
   - ❌ Some clicks expand, some navigate, some do actions
   - ✅ Clicks always reveal more; actions are buttons

4. **Summary-First Loading**
   - Show summary immediately, load details on demand
   - ❌ Loading spinner until all nested data arrives
   - ✅ Summary visible, children load when requested

### P1: Required

5. **Breadcrumb Navigation**
   - Path must be visible for depth > 1
   - Each breadcrumb segment clickable

6. **Sibling Navigation**
   - From detail view, can navigate to siblings
   - "Next/Previous" or sibling list visible

7. **Depth Indication**
   - Visual cue that more detail exists
   - Chevrons, "..." indicators, expandable icons

### P2: Advisory

8. **Animation Feedback**
   - Drill-down shows transition (150-300ms)
   - Helps user track context change

9. **Keyboard Navigation**
   - Escape = go up one level
   - Enter = drill into focused item

---

## 🔍 Anti-Patterns to Detect

### 1. Flat Sibling Pages
```
❌ BAD: /projects, /documents, /expenses as siblings
✅ GOOD: /projects/:id/documents, /projects/:id/expenses
```

### 2. Modal Hell
```
❌ BAD: Click opens modal, click in modal opens another modal
✅ GOOD: Click expands in-place or slides panel, context preserved
```

### 3. Tab Overload
```
❌ BAD: 7 tabs with no drill-down within each
✅ GOOD: 3 tabs, each with infinite drill-down depth
```

### 4. Static Dashboards
```
❌ BAD: Dashboard with metrics that aren't clickable
✅ GOOD: Every metric drills into its breakdown
```

### 5. Lost Context
```
❌ BAD: Navigate to detail, no way back except browser back
✅ GOOD: Breadcrumb always visible, direct navigation to any ancestor
```

---

## 📋 Pre-Generation Checklist

Before generating any UI code, answer these:

```markdown
## Progressive Disclosure Declaration

### Summary View
- [ ] What shows at first glance?
- [ ] What 2-3 key metrics are visible?
- [ ] What's the primary identifier?

### Drill-Down Structure  
- [ ] What entities can user click to expand?
- [ ] What's the click behavior (expand/panel/navigate)?
- [ ] How deep can user drill?

### Context Preservation
- [ ] How does user know where they are?
- [ ] Can user navigate back up?
- [ ] Is parent context still visible?

### Related Views
- [ ] What siblings exist at this level?
- [ ] How does user navigate to siblings?
- [ ] What's the parent view?

### Loading Strategy
- [ ] What loads immediately (summary)?
- [ ] What loads on-demand (detail)?
- [ ] What's the loading indicator?
```

---

## 🔗 Integration with UX Validation Pipeline

This skill defines **pipeline rules** (required declarations before generation), not just **governance gates** (validation after generation).

**In the UX Validation Pipeline:**

1. **Pre-Classification Hook**: Before classifying component type, check if declarations exist
2. **Declaration Requirement**: If UI task, must have completed Progressive Disclosure Declaration
3. **Gate Enhancement**: ComposabilityGate validates the declaration was followed

```python
# Pipeline integration
if is_ui_task(task):
    declaration = get_progressive_disclosure_declaration(task)
    if not declaration.is_complete():
        return ValidationResult(
            passed=False,
            message="Progressive Disclosure Declaration required before code generation",
            required_fields=declaration.missing_fields()
        )
```

---

## 📚 See Also

- `skills/ux-governance/SKILL.md` - P0/P1 UX rules
- `skills/ui-design-validation/SKILL.md` - Visual design rules
- `skills/frontend-composability/SKILL.md` - Component architecture
- `docs/specs/vislzr-spec.md` - VISLZR specification (origin of Wander pattern)
- `docs/plans/ux-validation-pipeline-spec.md` - Full pipeline spec
