---
title: Skill Definition Standard
version: 1.0.0
created: 2026-01-31
status: active
---

# Skill Definition Standard

Skills are machine-readable instructions that tell autonomous agents HOW to accomplish specific tasks within a service's domain.

## File Format

Skills are defined in YAML files with the `.yaml` extension, stored in `/docs/service-spec/skills/`.

## Schema

```yaml
# Required metadata
name: string           # Unique identifier (kebab-case)
version: string        # Semantic version
domain: string         # Service domain (commandcentral, pipelzr, vislzr, idealzr)
category: string       # Category (frontend, backend, integration, testing)
description: string    # Human-readable description

# Trigger patterns for skill matching
triggers:
  - pattern: string    # Regex or keyword pattern
    weight: number     # Optional: priority (higher = more specific)

# Required context for execution
context_required:
  api_reference:       # List of API paths needed
    - string
  domain_models:       # List of entity names needed
    - string
  patterns:            # List of patterns/libraries needed
    - string
  dependencies:        # External packages required
    - string

# Expected outputs from this skill
outputs:
  - type: string       # component, hook, service, test, etc.
    path: string       # Expected file path pattern
    template: string   # Optional: template file reference

# Pre-conditions that must be true
preconditions:
  - check: string      # Condition to verify
    message: string    # Error message if not met

# Step-by-step instructions for the agent
instructions:
  - step: number
    action: string     # What to do
    details: string    # How to do it

# Examples for few-shot learning
examples:
  - input: string      # Example task description
    reference: string  # Path to example implementation
    notes: string      # Optional context

# Validation rules to verify output
validation:
  - check: string      # Validation type
    config: object     # Validation configuration

# Related skills
related_skills:
  - string             # Names of related skills
```

## Full Example

```yaml
name: commandcentral-auth-frontend
version: 1.0.0
domain: commandcentral
category: frontend
description: |
  Creates authentication UI components for CommandCentral including
  login forms, registration forms, protected routes, and auth hooks.

triggers:
  - pattern: "login page|login form|authentication UI"
    weight: 100
  - pattern: "register page|signup form"
    weight: 100
  - pattern: "protected route|auth guard"
    weight: 80
  - pattern: "auth|authentication"
    weight: 50

context_required:
  api_reference:
    - /api/v1/auth/login
    - /api/v1/auth/register
    - /api/v1/auth/me
    - /api/v1/auth/logout
  domain_models:
    - User
    - Token
  patterns:
    - react-hook-form
    - zod-validation
    - shadcn-ui
    - zustand-persist
  dependencies:
    - react-hook-form
    - zod
    - @hookform/resolvers

outputs:
  - type: page
    path: src/pages/LoginPage.tsx
  - type: page
    path: src/pages/RegisterPage.tsx
  - type: component
    path: src/components/auth/LoginForm.tsx
  - type: component
    path: src/components/auth/RegisterForm.tsx
  - type: component
    path: src/components/auth/ProtectedRoute.tsx
  - type: hook
    path: src/hooks/useAuth.ts
  - type: store
    path: src/stores/authStore.ts

preconditions:
  - check: project_initialized
    message: "Frontend project must be initialized with Vite + React"
  - check: shadcn_installed
    message: "shadcn/ui must be installed and configured"

instructions:
  - step: 1
    action: Create authStore with Zustand
    details: |
      Create src/stores/authStore.ts with:
      - user, token, isAuthenticated state
      - login, logout, setUser actions
      - Persist token to localStorage using zustand/middleware

  - step: 2
    action: Create useAuth hook
    details: |
      Create src/hooks/useAuth.ts that wraps authStore and provides:
      - login(email, password) - calls API and updates store
      - logout() - clears store and redirects
      - register(email, password, name) - calls API

  - step: 3
    action: Create LoginForm component
    details: |
      Use react-hook-form with zod validation:
      - Email field with email validation
      - Password field with min 8 chars
      - Submit button with loading state
      - Error display for API errors

  - step: 4
    action: Create LoginPage
    details: |
      Wrap LoginForm in a Card component:
      - Center on page with max-w-md
      - Link to register page
      - Redirect to /dashboard on success

  - step: 5
    action: Create ProtectedRoute component
    details: |
      Wrap routes that require auth:
      - Check authStore.isAuthenticated
      - Redirect to /login with returnUrl if not authenticated
      - Show loading spinner while checking

examples:
  - input: "Create a login page with email and password"
    reference: examples/auth/login-page.tsx
    notes: Uses shadcn Card, Input, Button components

  - input: "Add auth protection to routes"
    reference: examples/auth/protected-route.tsx
    notes: Wraps React Router Outlet

validation:
  - check: typescript_compiles
    config:
      strict: true
  - check: no_eslint_errors
    config:
      extends: ["react-app"]
  - check: renders_without_crash
    config:
      test_file: "*.test.tsx"
  - check: api_calls_correct
    config:
      endpoints:
        - POST /api/v1/auth/login
        - POST /api/v1/auth/register

related_skills:
  - commandcentral-user-menu
  - commandcentral-profile-page
```

## Skill Categories

| Category | Description |
|----------|-------------|
| frontend | React components, pages, hooks, stores |
| backend | API endpoints, services, models |
| integration | Cross-service communication |
| testing | Test files, test utilities |
| infrastructure | Config, deployment, CI/CD |

## Trigger Matching

PIPELZR uses trigger patterns to match tasks to skills:

1. Extract keywords from task description
2. Match against all skill triggers (regex)
3. Score matches by weight
4. Select highest-scoring skill(s)
5. If multiple skills match, combine context

## Context Loading

When a skill is matched:

1. Load `api_reference` sections from service's api-reference.md
2. Load `domain_models` from service's domain-model.md
3. Load `patterns` from service's patterns.md
4. Combine into agent context window

## Validation

Before marking a skill-based task complete:

1. Run all validation checks from skill definition
2. Verify all expected outputs exist
3. Verify TypeScript compiles (if applicable)
4. Verify no ESLint errors (if applicable)
5. Run any custom validation scripts
