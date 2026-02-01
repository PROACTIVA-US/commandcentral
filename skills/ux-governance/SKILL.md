---
name: ux-governance
status: active
category: governance
description: Information architecture, role visibility, cognitive load limits, task flow continuity. UX principles for coherent user experiences.
updated: 2026-01-31 09:40
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
  - type: file_write
    description: May modify files
  - type: git_commit
    description: May create git commits
  - type: api_call
    description: May call external APIs
  - type: database_write
    description: May modify database
  auth_scopes:
  - scope: file:write
    required: true
  - scope: git:commit
    required: false
  timeouts:
    default_ms: 30000
    max_ms: 180000
---
# UX Governance Skill

> **Purpose**: Enforce user experience principles before, during, and after code generation to prevent disjointed, confusing, or unusable interfaces.

---

## 🚨 P0 Rules (Blocking - Must Pass Before Commit)

### 1. Information Architecture Coherence
**Rule**: Related data entities MUST be accessible from each other.

**Validation**:
- If entity A references entity B, navigation from A→B must exist
- "Orphan screens" with no contextual navigation are forbidden
- Documents, images, notes MUST be attachable to their parent entities (projects, vendors, properties)

**Anti-pattern detected in PropertyManager**:
```
❌ Documents page separate from Projects, Maintenance, Vendors
❌ Expenses separate from Projects they belong to
❌ Stakeholder input global instead of per-project
```

**Correct pattern**:
```
✅ Project detail → Documents tab → Project-specific docs
✅ Project detail → Expenses tab → Project costs
✅ Project detail → Stakeholders tab → Per-project feedback
```

### 2. Role-Based Feature Visibility Matrix
**Rule**: Every role MUST have validated access to features they need.

**Validation checklist**:
| Role | Must See | Must NOT See |
|------|----------|--------------|
| Owner | Vendors, Financials, Projects, Maintenance | Tenant personal data |
| PM | All operational data, Vendors, Tenants | Sensitive owner financials |
| Tenant | Their payments, maintenance requests | Other tenant data |

**Anti-pattern**:
```
❌ Owner cannot see Vendors (Layout.tsx: roles: ['pm'])
❌ Owner welcome page lacks property overview
```

### 3. Visual Data Consistency
**Rule**: Data visualization MUST follow consistent semantic meaning.

**Validation**:
- Green = positive/increase/good
- Red = negative/decrease/bad  
- Direction indicators must match semantic meaning
- Labels must match visual representation

**Anti-pattern**:
```
❌ Showing rental income as green chart but red/down arrow
❌ "Total Expenses" with positive green styling
```

### 4. Personalization Context Display
**Rule**: User identity and context MUST be prominently displayed.

**Validation**:
- Logged-in user's name visible on dashboard
- Role-specific greeting and context
- Property/project names shown, not generic "property"

**Anti-pattern**:
```
❌ Dashboard shows "property" instead of "123 Main St"
❌ Owner page shows generic welcome instead of "Welcome, Shanie"
```

---

## 🟡 P1 Rules (Required - Must Address Before Release)

### 5. Feature Importance Hierarchy
**Rule**: High-value features MUST be placed proportionally high in navigation.

**Validation scoring**:
| Frequency of Use | Importance | Minimum Position |
|------------------|------------|------------------|
| Daily | Critical | Top 3 nav items |
| Weekly | High | Top 5 nav items |
| Monthly | Medium | Below fold OK |
| Rarely | Low | Settings/overflow OK |

**Anti-pattern**:
```
❌ AI Assistant (high value) placed below Settings (low frequency)
❌ Financials (owner's primary concern) at bottom
```

### 6. Cognitive Load Limit
**Rule**: No more than 5±2 primary tabs per screen.

**Validation**:
- Count tabs per view, alert if > 7
- Nested tabs count toward total
- Prefer progressive disclosure over flat tabs

**Anti-pattern**:
```
❌ Financials: overview + property + rental + tax + projections (5 tabs)
   PLUS projections subtabs: keepvssell + mortgage (2 more)
   = 7 cognitive items
❌ Communication hub with multiple unneeded tabs
```

### 7. Task Flow Continuity  
**Rule**: Related tasks MUST be completable without context switching.

**Validation**:
- Creating an entity should allow attaching related data immediately
- No separate modals for sub-steps of same workflow
- "Save and continue" patterns for multi-step processes

**Anti-pattern**:
```
❌ Separate modal for routine tasks vs one-time tasks
❌ Create project → close modal → reopen to add phases
```

---

## 🔵 P2 Rules (Advisory - Flag for Review)

### 8. Empty State Guidance
**Rule**: Empty states MUST guide user to next action.

**Validation**:
- Every list has empty state component
- Empty state includes call-to-action
- No bare "No items" text

### 9. Error State Clarity
**Rule**: Error states MUST be actionable.

**Validation**:
- Error messages include what went wrong
- Error messages include how to fix
- No generic "Something went wrong"

### 10. Mobile Responsiveness Parity
**Rule**: Mobile experience MUST maintain feature parity for P0/P1 features.

**Validation**:
- Critical workflows accessible on mobile
- Touch targets minimum 44x44px
- No horizontal scroll for primary content

---

## 📋 Pre-Flight Checklist

Before any UI/UX commit, verify:

```markdown
## UX Pre-Flight

### P0 (Blocking)
- [ ] Information architecture coherence validated
- [ ] Role visibility matrix checked
- [ ] Data visualization semantics consistent
- [ ] Personalization context displayed

### P1 (Required)
- [ ] Feature importance hierarchy respected
- [ ] Cognitive load under 7 items per view
- [ ] Task flows don't require context switching

### P2 (Advisory)
- [ ] Empty states guide to action
- [ ] Error states are actionable
- [ ] Mobile responsiveness maintained
```

---

## 🔍 Detection Keywords

Trigger this skill when task contains:
- `page`, `dashboard`, `component`, `modal`, `tab`, `navigation`
- `user experience`, `UX`, `UI`, `interface`, `layout`
- `role`, `permission`, `visibility`, `access`
- `chart`, `graph`, `visualization`, `metrics`, `display`
- `form`, `wizard`, `workflow`, `multi-step`

---

## 📚 Reference Examples

### Good: CC4 VenturesPage
- Regime tabs respect cognitive load (3 items)
- IntakeWizard maintains context through 5-step flow
- Canvas shows contextual regime badges on nodes
- Kill conditions visible where relevant

### Bad: PropertyManager Financials
- 5 main tabs + 2 subtabs = cognitive overload
- Data scattered across disconnected views
- Owner's primary concerns buried below
- Visualization semantics inconsistent
