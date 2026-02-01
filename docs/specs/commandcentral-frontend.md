# CommandCentral Frontend Spec

## Executive Summary

Build a React + TypeScript frontend for CommandCentral that provides unified navigation across 4 microservices: CommandCentral (governance), IDEALZR (strategy), PIPELZR (execution), and VISLZR (visualization). The frontend features a dashboard with cross-service stats, global search, real-time activity feed, and user settings.

## Tech Stack

- React 18 + TypeScript + Vite
- Tailwind CSS + shadcn/ui components
- Zustand for state management
- TanStack Query (React Query) for data fetching
- React Router v6 for routing
- Axios for API clients
- @xyflow/react for canvas visualization

## Backend Services

| Service | Port | Responsibility |
|---------|------|----------------|
| CommandCentral | 8000 | Auth, projects, decisions, audit, state |
| PIPELZR | 8001 | Tasks, pipelines, agents, skills |
| VISLZR | 8002 | Canvas, nodes, relationships, exploration |
| IDEALZR | 8003 | Goals, hypotheses, evidence, forecasts, ideas |

---

## Tasks

### Batch 1: Project Foundation

- [ ] **Task 1: Initialize Vite + React + TypeScript project**
  - Create `/frontend` directory in CommandCentral root
  - Run `npm create vite@latest . -- --template react-ts`
  - Update `package.json` with project name "commandcentral-frontend"
  - Install core dependencies: `react-router-dom`, `axios`, `zustand`, `@tanstack/react-query`
  - Configure `vite.config.ts` with path aliases (@/ for src/)
  - Create basic folder structure: api/, components/, features/, stores/, pages/, routes/
  - **Acceptance criteria:**
    - `npm run dev` starts without errors
    - TypeScript compilation succeeds
    - Path aliases work (@/components resolves correctly)
  - **Complexity:** simple
  - **Files:** frontend/package.json, frontend/vite.config.ts, frontend/tsconfig.json

- [ ] **Task 2: Configure Tailwind CSS + shadcn/ui**
  - Install Tailwind CSS: `npm install -D tailwindcss postcss autoprefixer`
  - Initialize Tailwind: `npx tailwindcss init -p`
  - Configure `tailwind.config.js` with content paths and theme
  - Create `src/styles/globals.css` with Tailwind directives
  - Initialize shadcn/ui: `npx shadcn@latest init`
  - Install base shadcn components: button, card, input, dialog, tabs, dropdown-menu, toast
  - Configure CSS variables for theming (light/dark)
  - **Acceptance criteria:**
    - Tailwind classes apply correctly
    - shadcn Button component renders with correct styling
    - Theme variables are defined
  - **Complexity:** simple
  - **Files:** frontend/tailwind.config.js, frontend/postcss.config.js, frontend/src/styles/globals.css, frontend/components.json

- [ ] **Task 3: Set up base API client with JWT interceptors**
  - Create `src/api/baseClient.ts` with Axios instance factory
  - Define SERVICE_URLS constant for all 4 backend ports
  - Implement request interceptor to add Authorization header from auth store
  - Implement response interceptor for 401 handling (logout on unauthorized)
  - Add request/response logging in development mode
  - Create `src/api/types.ts` with shared API types (PaginatedResponse, ErrorResponse)
  - **Acceptance criteria:**
    - createServiceClient('commandcentral') returns configured Axios instance
    - JWT token is automatically added to requests when available
    - 401 responses trigger logout
  - **Complexity:** medium
  - **Files:** frontend/src/api/baseClient.ts, frontend/src/api/types.ts, frontend/src/api/interceptors.ts

---

### Batch 2: Core Layout & State
**Depends on:** Batch 1

- [ ] **Task 4: Create Zustand stores**
  - Create `src/stores/authStore.ts` with user, token, isAuthenticated state
    - Actions: login, logout, setUser, refreshToken
    - Persist token to localStorage
  - Create `src/stores/uiStore.ts` with activeService, sidebarCollapsed, theme
    - Actions: setActiveService, toggleSidebar, setTheme
  - Create `src/stores/projectStore.ts` with projects, activeProjectId
    - Actions: fetchProjects, setActiveProject, createProject
  - Create `src/stores/index.ts` exporting all stores
  - **Acceptance criteria:**
    - authStore persists token across page refreshes
    - uiStore tracks current active service tab
    - All stores have TypeScript types
  - **Complexity:** medium
  - **Files:** frontend/src/stores/authStore.ts, frontend/src/stores/uiStore.ts, frontend/src/stores/projectStore.ts, frontend/src/stores/index.ts

- [ ] **Task 5: Build AppShell, Header, TabNavigation components**
  - Create `src/components/layout/AppShell.tsx` as main layout wrapper
    - Renders Header at top, content area with Outlet
    - Handles responsive layout
  - Create `src/components/layout/Header.tsx`
    - Contains TabNavigation, GlobalSearchTrigger, NotificationBell, UserMenu
    - Fixed position at top
  - Create `src/components/layout/TabNavigation.tsx`
    - Tabs: Dashboard, IDEALZR, PIPELZR, VISLZR, Governance
    - Uses React Router NavLink for active state
    - Icons from lucide-react: LayoutDashboard, Target, GitBranch, Network, Shield
  - Create `src/components/layout/ServiceStatusBar.tsx`
    - Shows health status of all 4 backend services
    - Green/red indicators
  - **Acceptance criteria:**
    - AppShell renders with header and content area
    - Tab navigation shows active state correctly
    - Clicking tabs changes URL
  - **Complexity:** medium
  - **Files:** frontend/src/components/layout/AppShell.tsx, frontend/src/components/layout/Header.tsx, frontend/src/components/layout/TabNavigation.tsx, frontend/src/components/layout/ServiceStatusBar.tsx

- [ ] **Task 6: Configure React Router with all routes**
  - Create `src/routes/routes.tsx` with createBrowserRouter
  - Define route structure:
    - `/` redirects to `/dashboard`
    - `/login`, `/register` (public)
    - `/dashboard` (home)
    - `/idealzr/*` (goals, hypotheses, evidence, forecasts, ventures, ideas)
    - `/pipelzr/*` (tasks, pipelines, agents, skills)
    - `/vislzr/*` (canvas, explore)
    - `/commandcentral/*` (governance, decisions, audit, arena)
    - `/settings`, `/profile`
  - Create `src/components/auth/ProtectedRoute.tsx` for auth guard
  - Update `src/App.tsx` to use RouterProvider
  - **Acceptance criteria:**
    - All routes are accessible
    - Protected routes redirect to /login when unauthenticated
    - Nested routes render within parent layouts
  - **Complexity:** medium
  - **Files:** frontend/src/routes/routes.tsx, frontend/src/components/auth/ProtectedRoute.tsx, frontend/src/App.tsx

---

### Batch 3: Authentication
**Depends on:** Task 4, Task 5, Task 6

- [ ] **Task 7: Create commandCentralClient API**
  - Create `src/api/clients/commandCentralClient.ts`
  - Implement auth endpoints:
    - login(email, password) -> TokenResponse
    - register(email, password, name) -> UserResponse
    - getMe() -> UserResponse
    - logout() -> void
  - Implement projects endpoints:
    - getProjects(params) -> PaginatedResponse<Project>
    - getProject(id) -> Project
    - createProject(data) -> Project
  - Implement events endpoints:
    - getEvents(params) -> EventsResponse
  - Define TypeScript interfaces for all request/response types
  - **Acceptance criteria:**
    - All endpoints are callable
    - TypeScript types match backend schemas
    - Errors are properly typed
  - **Complexity:** medium
  - **Files:** frontend/src/api/clients/commandCentralClient.ts, frontend/src/types/commandcentral.ts

- [ ] **Task 8: Build LoginPage and RegisterPage**
  - Create `src/pages/LoginPage.tsx`
    - Email and password inputs with react-hook-form
    - Submit calls authStore.login
    - Redirects to /dashboard on success
    - Shows error toast on failure
  - Create `src/pages/RegisterPage.tsx`
    - Name, email, password, confirm password inputs
    - Validation with zod
    - Submit calls commandCentralClient.register
    - Redirects to /login on success
  - Create `src/components/auth/LoginForm.tsx` and `RegisterForm.tsx`
  - Style with shadcn Card, Input, Button components
  - **Acceptance criteria:**
    - Login form submits and stores token
    - Register form creates account
    - Validation errors display correctly
    - Loading states shown during submission
  - **Complexity:** medium
  - **Files:** frontend/src/pages/LoginPage.tsx, frontend/src/pages/RegisterPage.tsx, frontend/src/components/auth/LoginForm.tsx, frontend/src/components/auth/RegisterForm.tsx

- [ ] **Task 9: Implement ProtectedRoute + UserMenu**
  - Update `src/components/auth/ProtectedRoute.tsx`
    - Check authStore.isAuthenticated
    - Redirect to /login with return URL if not authenticated
    - Show loading spinner while checking auth
  - Create `src/components/user/UserMenu.tsx`
    - Shows user avatar/initials
    - Dropdown with: Profile, Settings, Logout
    - Logout clears authStore and redirects to /login
  - Create `src/components/user/UserAvatar.tsx`
    - Displays user initials or image
  - **Acceptance criteria:**
    - Unauthenticated users cannot access protected routes
    - UserMenu displays current user info
    - Logout clears session and redirects
  - **Complexity:** simple
  - **Files:** frontend/src/components/auth/ProtectedRoute.tsx, frontend/src/components/user/UserMenu.tsx, frontend/src/components/user/UserAvatar.tsx

---

### Batch 4: Dashboard
**Depends on:** Batch 3

- [ ] **Task 10: Create all 4 service API clients**
  - Create `src/api/clients/idealzrClient.ts`
    - Goals: getGoals, getGoal, createGoal, updateGoal, transitionGoal
    - Hypotheses: getHypotheses, getHypothesis, createHypothesis, updateHypothesis
    - Evidence: getEvidence, createEvidence
  - Create `src/api/clients/pipelzrClient.ts`
    - Tasks: getTasks, getTask, createTask, updateTask, transitionTask
    - Pipelines: getPipelines, getPipeline, runPipeline, cancelPipeline
    - Agents: getAgents, getAgent
  - Create `src/api/clients/vislzrClient.ts`
    - Nodes: getNodes, getNode, createNode, updateNode
    - Canvas: getLayouts, saveLayout
    - Exploration: explore
  - Create corresponding type files in `src/types/`
  - **Acceptance criteria:**
    - All clients are importable and typed
    - Endpoints match backend API structure
  - **Complexity:** medium
  - **Files:** frontend/src/api/clients/idealzrClient.ts, frontend/src/api/clients/pipelzrClient.ts, frontend/src/api/clients/vislzrClient.ts, frontend/src/types/idealzr.ts, frontend/src/types/pipelzr.ts, frontend/src/types/vislzr.ts

- [ ] **Task 11: Build DashboardPage with widget grid**
  - Create `src/pages/DashboardPage.tsx`
    - Header with "Dashboard" title and ProjectSelector
    - Stats row (4 columns): Active Goals, Running Tasks, Pipelines, Hypotheses
    - Main grid (3 columns):
      - Left: GoalsSummaryWidget, HypothesesWidget
      - Center: TasksSummaryWidget, PipelineStatusWidget
      - Right: RecentActivityWidget, QuickActionsWidget
  - Create `src/components/projects/ProjectSelector.tsx`
    - Dropdown to select active project
    - Uses projectStore
  - Use TanStack Query for data fetching with proper caching
  - **Acceptance criteria:**
    - Dashboard renders with placeholder widgets
    - ProjectSelector changes active project
    - Responsive grid layout works on mobile
  - **Complexity:** medium
  - **Files:** frontend/src/pages/DashboardPage.tsx, frontend/src/components/projects/ProjectSelector.tsx

- [ ] **Task 12: Implement CrossServiceStatsWidget**
  - Create `src/components/dashboard/CrossServiceStatsWidget.tsx`
  - Fetches in parallel from all 4 services:
    - Active goals count from IDEALZR
    - Running tasks count from PIPELZR
    - Active pipelines count from PIPELZR
    - Open hypotheses count from IDEALZR
  - Create `src/components/dashboard/StatCard.tsx`
    - Icon, title, value, optional trend indicator
    - Click navigates to relevant service
  - Use useQueries for parallel fetching
  - 30-second auto-refresh
  - **Acceptance criteria:**
    - Stats load from all services
    - Shows loading skeletons while fetching
    - Handles service errors gracefully (shows N/A)
  - **Complexity:** medium
  - **Files:** frontend/src/components/dashboard/CrossServiceStatsWidget.tsx, frontend/src/components/dashboard/StatCard.tsx

- [ ] **Task 13: Build RecentActivityWidget**
  - Create `src/components/dashboard/RecentActivityWidget.tsx`
  - Fetches recent events from CommandCentral /api/v1/events
  - Create `src/components/activity/ActivityItem.tsx`
    - Icon based on event type
    - Description, timestamp, entity link
  - Shows last 10 events
  - "View all" link to activity page
  - **Acceptance criteria:**
    - Activity items render with correct formatting
    - Timestamps are relative (e.g., "2 minutes ago")
    - Clicking item navigates to entity
  - **Complexity:** simple
  - **Files:** frontend/src/components/dashboard/RecentActivityWidget.tsx, frontend/src/components/activity/ActivityItem.tsx

---

### Batch 5: Service Tabs
**Depends on:** Batch 4

- [ ] **Task 14: IDEALZR - Goals and Hypotheses pages**
  - Create `src/features/idealzr/pages/GoalsPage.tsx`
    - List view with filters (state, priority)
    - GoalCard component showing title, state, progress
    - Create goal button opening modal
  - Create `src/features/idealzr/pages/HypothesesPage.tsx`
    - Kanban view by state (investigating, validated, invalidated)
    - HypothesisCard with confidence slider
    - Link evidence to hypothesis
  - Create `src/features/idealzr/components/GoalCard.tsx`
  - Create `src/features/idealzr/components/HypothesisCard.tsx`
  - Create `src/features/idealzr/components/ConfidenceSlider.tsx`
  - Create sub-navigation for IDEALZR tab
  - **Acceptance criteria:**
    - Goals list renders with real data
    - Hypotheses kanban allows drag-and-drop state changes
    - Forms validate and submit correctly
  - **Complexity:** complex
  - **Files:** frontend/src/features/idealzr/pages/GoalsPage.tsx, frontend/src/features/idealzr/pages/HypothesesPage.tsx, frontend/src/features/idealzr/components/GoalCard.tsx, frontend/src/features/idealzr/components/HypothesisCard.tsx, frontend/src/features/idealzr/components/ConfidenceSlider.tsx

- [ ] **Task 15: PIPELZR - Tasks and Pipelines pages**
  - Create `src/features/pipelzr/pages/TasksPage.tsx`
    - Kanban view by state (pending, running, completed, failed)
    - TaskCard with execution info
    - Create task modal
  - Create `src/features/pipelzr/pages/PipelinesPage.tsx`
    - List of pipelines with progress bars
    - Run/cancel/retry actions
    - Pipeline detail drawer
  - Create `src/features/pipelzr/components/TaskCard.tsx`
  - Create `src/features/pipelzr/components/TaskKanban.tsx`
  - Create `src/features/pipelzr/components/PipelineCard.tsx`
  - Create `src/features/pipelzr/components/PipelineProgress.tsx`
  - Create sub-navigation for PIPELZR tab
  - **Acceptance criteria:**
    - Tasks kanban renders with real data
    - Pipeline progress updates in real-time
    - Actions trigger correct API calls
  - **Complexity:** complex
  - **Files:** frontend/src/features/pipelzr/pages/TasksPage.tsx, frontend/src/features/pipelzr/pages/PipelinesPage.tsx, frontend/src/features/pipelzr/components/TaskCard.tsx, frontend/src/features/pipelzr/components/TaskKanban.tsx, frontend/src/features/pipelzr/components/PipelineCard.tsx, frontend/src/features/pipelzr/components/PipelineProgress.tsx

- [ ] **Task 16: VISLZR - Canvas page with @xyflow/react**
  - Install @xyflow/react: `npm install @xyflow/react`
  - Create `src/features/vislzr/pages/CanvasPage.tsx`
    - Full-screen canvas with zoom/pan
    - Toolbar for adding nodes
    - MiniMap for navigation
  - Create `src/features/vislzr/components/Canvas.tsx`
    - Uses ReactFlow with custom node types
    - Handles node drag, connection creation
  - Create node components in `src/features/vislzr/components/nodes/`
    - GoalNode.tsx, TaskNode.tsx, HypothesisNode.tsx, IdeaNode.tsx
  - Create `src/features/vislzr/components/CanvasToolbar.tsx`
  - Create `src/features/vislzr/components/MiniMap.tsx`
  - **Acceptance criteria:**
    - Canvas renders with nodes from VISLZR API
    - Nodes are draggable and connectable
    - Layout saves to backend
  - **Complexity:** complex
  - **Files:** frontend/src/features/vislzr/pages/CanvasPage.tsx, frontend/src/features/vislzr/components/Canvas.tsx, frontend/src/features/vislzr/components/nodes/GoalNode.tsx, frontend/src/features/vislzr/components/nodes/TaskNode.tsx, frontend/src/features/vislzr/components/CanvasToolbar.tsx, frontend/src/features/vislzr/components/MiniMap.tsx

- [ ] **Task 17: Governance - Decisions and Audit pages**
  - Create `src/features/commandcentral/pages/DecisionsPage.tsx`
    - List of decisions with state badges
    - Decision detail view
    - Transition buttons based on allowed transitions
  - Create `src/features/commandcentral/pages/AuditPage.tsx`
    - Filterable audit log table
    - Event type, entity, user, timestamp columns
    - Export to CSV
  - Create `src/features/commandcentral/components/DecisionCard.tsx`
  - Create `src/features/commandcentral/components/AuditLogViewer.tsx`
  - Create sub-navigation for Governance tab
  - **Acceptance criteria:**
    - Decisions list shows current state
    - State transitions work correctly
    - Audit log filters and paginates
  - **Complexity:** medium
  - **Files:** frontend/src/features/commandcentral/pages/DecisionsPage.tsx, frontend/src/features/commandcentral/pages/AuditPage.tsx, frontend/src/features/commandcentral/components/DecisionCard.tsx, frontend/src/features/commandcentral/components/AuditLogViewer.tsx

- [ ] **Task 18: AI Arena - Multi-model deliberation**
  - Create `src/features/arena/pages/ArenaPage.tsx`
    - List of arena sessions
    - Create session button with topic input
    - Session cards showing status, participants, message count
  - Create `src/features/arena/pages/ArenaSessionPage.tsx`
    - Multi-agent chat view
    - Messages grouped by agent with provider badges
    - Input for user messages
    - Preflight status indicator
  - Create `src/features/arena/components/SessionCard.tsx`
  - Create `src/features/arena/components/AgentMessage.tsx`
    - Agent avatar/icon by provider
    - Message content with markdown
    - Timestamp and metadata
  - Create `src/features/arena/components/PreflightStatus.tsx`
    - Shows which models are ready/failed
    - Latency indicators
  - Create `src/features/arena/components/AgentSelector.tsx`
    - Select models for new session
    - Shows available flagship models
  - Create `src/api/clients/arenaClient.ts`
    - createSession, getSession, getSessions
    - chat, preflight, getMessages
  - Add Arena to Governance sub-navigation
  - **Acceptance criteria:**
    - Sessions list with create/view actions
    - Real-time chat with multiple AI agents
    - Preflight shows model availability
    - Messages display with agent attribution
  - **Complexity:** complex
  - **Files:** frontend/src/features/arena/pages/ArenaPage.tsx, frontend/src/features/arena/pages/ArenaSessionPage.tsx, frontend/src/features/arena/components/SessionCard.tsx, frontend/src/features/arena/components/AgentMessage.tsx, frontend/src/features/arena/components/PreflightStatus.tsx, frontend/src/api/clients/arenaClient.ts

---

### Batch 6: Global Features
**Depends on:** Batch 5

- [ ] **Task 19: Global search (Cmd+K) with cross-service results**
  - Install cmdk: `npm install cmdk`
  - Create `src/stores/searchStore.ts`
    - query, results, isSearching, filters, recentSearches
    - Actions: search, setFilters, clearSearch
  - Create `src/components/search/GlobalSearchBar.tsx`
    - Uses cmdk Command component
    - Cmd+K keyboard shortcut to open
    - Debounced search (300ms)
  - Create `src/components/search/SearchResults.tsx`
    - Groups results by service
    - Service badges with colors
  - Create `src/api/search.ts`
    - searchAll() - parallel search across all 4 services
  - **Acceptance criteria:**
    - Cmd+K opens search dialog
    - Search returns results from all services
    - Selecting result navigates to entity
    - Recent searches persist
  - **Complexity:** complex
  - **Files:** frontend/src/stores/searchStore.ts, frontend/src/components/search/GlobalSearchBar.tsx, frontend/src/components/search/SearchResults.tsx, frontend/src/components/search/SearchResultCard.tsx, frontend/src/api/search.ts

- [ ] **Task 20: Notification system with WebSocket**
  - Create `src/stores/notificationStore.ts`
    - notifications, unreadCount, isConnected
    - Actions: addNotification, markAsRead, markAllAsRead
  - Create `src/hooks/useWebSocket.ts`
    - Connects to CommandCentral /ws/events endpoint
    - Reconnects on disconnect
    - Parses events and dispatches to store
  - Create `src/components/activity/NotificationBell.tsx`
    - Bell icon with unread badge
    - Opens NotificationDropdown on click
  - Create `src/components/activity/NotificationDropdown.tsx`
    - List of recent notifications
    - Mark as read on click
    - "Mark all as read" action
  - Create `src/components/activity/ActivityFeed.tsx`
    - Full activity feed page
  - **Acceptance criteria:**
    - WebSocket connects on app load
    - New events appear in real-time
    - Unread count updates correctly
    - Notifications persist across navigation
  - **Complexity:** complex
  - **Files:** frontend/src/stores/notificationStore.ts, frontend/src/hooks/useWebSocket.ts, frontend/src/components/activity/NotificationBell.tsx, frontend/src/components/activity/NotificationDropdown.tsx, frontend/src/components/activity/ActivityFeed.tsx

- [ ] **Task 21: Settings and Profile pages**
  - Create `src/pages/SettingsPage.tsx`
    - Theme selector (light/dark/system)
    - Notification preferences
    - API key display (masked)
  - Create `src/pages/ProfilePage.tsx`
    - User info display
    - Edit name/email form
    - Change password form
  - Create `src/components/user/ProfileForm.tsx`
  - Create `src/components/user/PreferencesForm.tsx`
  - Persist preferences to localStorage
  - **Acceptance criteria:**
    - Theme changes apply immediately
    - Profile updates save to backend
    - Password change validates old password
  - **Complexity:** medium
  - **Files:** frontend/src/pages/SettingsPage.tsx, frontend/src/pages/ProfilePage.tsx, frontend/src/components/user/ProfileForm.tsx, frontend/src/components/user/PreferencesForm.tsx

---

### Batch 7: Polish
**Depends on:** Batch 6

- [ ] **Task 22: Loading states, error boundaries, dark mode**
  - Create `src/components/common/Skeleton.tsx` loading skeletons
  - Create `src/components/common/ErrorBoundary.tsx`
    - Catches React errors
    - Shows friendly error message
    - Retry button
  - Create `src/components/common/LoadingSpinner.tsx`
  - Implement dark mode in Tailwind config
    - Use CSS variables for colors
    - Respect system preference
    - Manual toggle in settings
  - Add loading states to all data-fetching components
  - Create `src/components/common/Toast.tsx` using shadcn toast
  - Add keyboard shortcuts documentation
  - **Acceptance criteria:**
    - All pages have loading states
    - Errors don't crash the app
    - Dark mode works correctly
    - Toasts appear for actions
  - **Complexity:** medium
  - **Files:** frontend/src/components/common/Skeleton.tsx, frontend/src/components/common/ErrorBoundary.tsx, frontend/src/components/common/LoadingSpinner.tsx, frontend/src/components/common/Toast.tsx, frontend/tailwind.config.js

---

## Implementation Notes

### API Response Patterns
All services use consistent response formats:
- Success: `{ data: T }` or `{ items: T[], total: number, page: number }`
- Error: `{ detail: string }` with appropriate HTTP status

### State Machine Integration
- Goals: DRAFT -> ACTIVE -> ON_HOLD -> ACHIEVED/ABANDONED
- Tasks: PENDING -> QUEUED -> RUNNING -> COMPLETED/FAILED
- Hypotheses: DRAFT -> INVESTIGATING -> VALIDATED/INVALIDATED
- Decisions: DRAFT -> ACTIVE -> DECIDED -> ARCHIVED

### WebSocket Events
Connect to `ws://localhost:8000/api/v1/events/stream?project_id={id}&token={jwt}`
Event types: entity_created, entity_updated, state_transition, task_completed, etc.

### Testing Strategy
- Unit tests with Vitest for stores and utilities
- Component tests with Testing Library for UI
- E2E tests with Playwright for critical flows
