---
name: ui-design-validation
status: active
category: validation
description: Visual hierarchy, semantic colors, spacing consistency, touch targets, focus states. Enforce design principles before code generation.
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
# UI Design Validation Skill

> **Purpose**: Enforce visual design principles, component consistency, and aesthetic quality standards before code generation.

---

## 🚨 P0 Rules (Blocking - Visual Correctness)

### 1. Semantic Color Mapping
**Rule**: Colors MUST convey consistent meaning across the application.

**Standard Palette**:
| Semantic | Color | Usage |
|----------|-------|-------|
| Success/Positive | Green (#22c55e) | Completed, increase, profit |
| Warning/Caution | Yellow/Orange (#f59e0b) | Pending, attention needed |
| Error/Negative | Red (#ef4444) | Failed, decrease, loss |
| Information/Neutral | Blue (#3b82f6) | Active, selected, info |
| Muted/Disabled | Gray (#64748b) | Inactive, secondary |

**Validation**:
```typescript
// ❌ BAD: Green for expenses (negative)
<span className="text-green-500">${expenses}</span>

// ✅ GOOD: Red for expenses
<span className="text-red-500">${expenses}</span>

// ❌ BAD: Red arrow for income increase
<ArrowUp className="text-red-500" /> +$500

// ✅ GOOD: Green arrow for income increase
<ArrowUp className="text-green-500" /> +$500
```

### 2. Visual Hierarchy Enforcement
**Rule**: Important elements MUST be visually prominent.

**Hierarchy levels**:
1. **Primary**: Largest, boldest, highest contrast (page title, main CTA)
2. **Secondary**: Medium emphasis (section headers, secondary buttons)
3. **Tertiary**: Lower emphasis (labels, helper text)
4. **Quaternary**: Minimal emphasis (timestamps, metadata)

**Validation**:
```typescript
// ❌ BAD: AI Assistant (high value) same weight as Settings
<NavItem icon={Sparkles}>AI Assistant</NavItem>  // Same as all others
<NavItem icon={Settings}>Settings</NavItem>

// ✅ GOOD: AI Assistant visually promoted
<NavItem icon={Sparkles} variant="primary" glow>AI Assistant</NavItem>
<NavItem icon={Settings} variant="muted">Settings</NavItem>
```

### 3. Data Display Alignment
**Rule**: Numerical data MUST be right-aligned; text MUST be left-aligned.

**Validation**:
```typescript
// ❌ BAD: Numbers left-aligned
<td className="text-left">$1,234.56</td>

// ✅ GOOD: Numbers right-aligned for comparison
<td className="text-right tabular-nums">$1,234.56</td>
```

### 4. Icon + Text Pairing
**Rule**: Icons MUST be paired with text labels for clarity.

**Exceptions**: Only universally understood icons (close X, hamburger menu, search magnifier) may appear without labels.

**Validation**:
```typescript
// ❌ BAD: Icon-only button (ambiguous)
<button><Trash2 /></button>

// ✅ GOOD: Icon with label
<button><Trash2 /> Delete</button>

// ✅ ACCEPTABLE: Universal icon with tooltip
<button title="Close"><X /></button>
```

---

## 🟡 P1 Rules (Required - Design Quality)

### 5. Spacing Consistency
**Rule**: Use consistent spacing scale (4px base: 4, 8, 12, 16, 24, 32, 48).

**Validation**:
```typescript
// ❌ BAD: Arbitrary spacing
<div className="gap-5 p-7 mt-3">  // 20px, 28px, 12px

// ✅ GOOD: Scale-consistent spacing  
<div className="gap-4 p-6 mt-2">  // 16px, 24px, 8px
```

### 6. Card Consistency
**Rule**: All cards in a view MUST share same border radius, shadow, padding.

**Validation**:
```typescript
// ❌ BAD: Inconsistent cards
<div className="rounded-lg shadow-md p-4">Card A</div>
<div className="rounded-xl shadow-sm p-6">Card B</div>

// ✅ GOOD: Consistent card pattern
<Card>Card A</Card>  // Uses shared component
<Card>Card B</Card>
```

### 7. Touch Target Size
**Rule**: Interactive elements MUST be minimum 44x44px on touch devices.

**Validation**:
```typescript
// ❌ BAD: Tiny touch target
<button className="w-6 h-6">+</button>

// ✅ GOOD: Adequate touch target
<button className="w-10 h-10 min-w-[44px] min-h-[44px]">+</button>
```

### 8. Loading State Consistency
**Rule**: All async operations MUST show consistent loading indicators.

**Pattern**:
- Skeleton for content loading
- Spinner for action pending
- Progress bar for long operations

### 9. Focus State Visibility
**Rule**: All interactive elements MUST have visible focus states.

**Validation**:
```typescript
// ❌ BAD: No focus indication
<button className="outline-none">Submit</button>

// ✅ GOOD: Visible focus ring
<button className="focus:ring-2 focus:ring-brand-orange focus:ring-offset-2">
  Submit
</button>
```

---

## 🔵 P2 Rules (Advisory - Polish)

### 10. Animation Consistency
**Rule**: Use consistent easing and duration (150ms for micro, 300ms for transitions).

### 11. Typography Scale
**Rule**: Use defined typography scale (xs, sm, base, lg, xl, 2xl, 3xl).

### 12. Dark Mode Support
**Rule**: Color choices MUST work in both light and dark modes.

---

## 📋 UI Design Checklist

Before any UI commit, verify:

```markdown
## UI Design Pre-Flight

### P0 (Blocking)
- [ ] Colors semantically correct (green=good, red=bad)
- [ ] Visual hierarchy reflects importance
- [ ] Numbers right-aligned, text left-aligned
- [ ] Icons have text labels (or are universal)

### P1 (Required)
- [ ] Spacing uses consistent scale
- [ ] Cards share consistent styling
- [ ] Touch targets ≥ 44px
- [ ] Loading states implemented
- [ ] Focus states visible

### P2 (Polish)
- [ ] Animations use consistent timing
- [ ] Typography uses defined scale
- [ ] Dark mode compatible
```

---

## 🔍 Detection Keywords

Trigger this skill when task contains:
- `style`, `design`, `color`, `theme`, `appearance`
- `button`, `card`, `modal`, `form`, `input`
- `icon`, `chart`, `graph`, `table`, `list`
- `animation`, `transition`, `hover`, `focus`
- `responsive`, `mobile`, `tablet`, `desktop`

---

## 📚 Component Patterns

### Good: Consistent Card
```typescript
export function Card({ children, className }: CardProps) {
  return (
    <div className={cn(
      "rounded-lg border border-slate-700/50",
      "bg-brand-dark/50 p-6",
      "shadow-lg",
      className
    )}>
      {children}
    </div>
  );
}
```

### Good: Semantic Metric Display
```typescript
export function MetricChange({ value, isPositive }: MetricProps) {
  return (
    <span className={cn(
      "flex items-center gap-1",
      isPositive ? "text-green-500" : "text-red-500"
    )}>
      {isPositive ? <ArrowUp size={14} /> : <ArrowDown size={14} />}
      {Math.abs(value)}%
    </span>
  );
}
```

### Bad: PropertyManager Financial Confusion
```typescript
// ❌ Rental income shown with confusing indicators
<div className="text-green-500">  {/* Green = good? */}
  Rental Income
  <span className="text-red-500">  {/* But red arrow?! */}
    <ArrowDown /> -5%
  </span>
</div>
```
