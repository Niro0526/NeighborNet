# NeighborNet AI — Frontend Progress Log

## Phase 1 — Foundation (Completed & Enhanced)

### 1. Overview & Setup
- **Scaffold**: Modern Vite + React 19 + TypeScript (strict mode) application.
- **Styling Architecture**: Tailwind CSS v4 alongside Mantine UI v7 (`@mantine/core`, `@mantine/hooks`).
- **Design Tokens**: Configured primary emerald green palette (`#16866A`), primary dark (`#09664F`), surface (`#FFFFFF`), background (`#F8FAF9`), and Inter typography.
- **Routing & State**: Set up `react-router-dom` v7 with workspace guards, `AuthContext`, and `OperationalContext` (Normal vs Disaster Mode).

### 2. Multi-Role Authentication & Workspace Switching Architecture
- **Single Account Multi-Role Support**:
  ```ts
  interface User {
    id: string;
    name: string;
    fullName: string;
    email: string;
    assignedRoles: UserRole[];
    activeRole: UserRole;
  }
  ```
- **Approved Roles**:
  - `FOOD_PROVIDER`
  - `RECIPIENT`
  - `VOLUNTEER`
  - `COORDINATOR` (privileged, non-self-assignable)
- **Multi-Role User Demonstration**:
  - `Ravi Mendis` (`USR-001`): Approved as both **Food Provider** (GreenBites Bistro) and **Volunteer Courier** (120 kg car courier).
  - Can switch between `/provider/dashboard` and `/volunteer/dashboard` without re-authenticating.
- **Single-Role Users**:
  - `Fathima Rizwan` (Food Provider), `Sister Mary Teresa` (NGO / Recipient), `Dinesh Mendis` (Volunteer), `Dr. Kaveen Jayawardena` (Coordinator).
- **Workspace Protection (`WorkspaceProtectedRoute`)**:
  - Intercepts requests to `/provider/*`, `/recipient/*`, `/volunteer/*`, and `/coordinator/*`.
  - Verifies approved membership in `user.assignedRoles`.
  - Seamlessly updates `user.activeRole` when a multi-role user navigates between authorized workspaces.
  - Displays a restricted access screen if an unapproved role is accessed.
- **Profile Dropdown Workspace Switcher**:
  - Workspace selector is integrated directly inside the profile dropdown (not permanently cluttering the sidebar).
  - Only appears for multi-role users (`assignedRoles.length > 1`). Single-role users see an approved role badge.
  - Persists across page reloads via `mockRepository` and `localStorage`.
- **Coordinator-Only Disaster Mode Authority**:
  - Global Disaster Response Mode can only be toggled by users with an approved `COORDINATOR` role.
  - Unauthorized users attempting to trigger disaster mode receive an explanatory permission warning modal.
  - Contextual emergency status banners appear in Food Provider, Recipient, and Volunteer dashboards when Disaster Mode is active.

### 3. Centralized Mock Data (`src/mockData/`)
All mock datasets are centralized, strongly-typed, and cross-referenced with realistic Sri Lankan locations (Moratuwa, Mount Lavinia, Dehiwala, Colombo):
- `users.ts`: Multi-role and single-role user models.
- `organizations.ts`: Verified restaurants, bakeries, supermarkets, and NGO shelters.
- `foodListings.ts`: Surplus listings with safe consumption windows and temperature guidelines.
- `resourceRequests.ts`: Community requests across normal and disaster relief categories.
- `volunteers.ts`: Volunteer couriers with independent vehicle classifications and availability.
- `deliveryTasks.ts`: Complete task state machine (`AVAILABLE` -> `ACCEPTED` -> `ARRIVED_PICKUP` -> `PICKED_UP` -> `ARRIVED_DELIVERY` -> `DELIVERED`).
- `disasterEvents.ts`: Monsoon emergency scenario in Lunawa Lagoon with affected zones and deficit summaries.
- `allocations.ts`: AI-assisted matching suggestions with compatibility percentages and rationales.
- `aiInsights.ts`: Simulated heuristics labeled as **Demo Recommendation — Simulated**.
- `notifications.ts`: Role-targeted alert stream.
- `activityLogs.ts`: System-wide audit trail and event ledger.
- `mapLocations.ts`: Coordinated geospatial markers for MapLibre GL.
- `analytics.ts`: Dynamic mathematical calculations derived directly from seed records.
- `scenarios.ts`: Interactive demo presets for ModelX demonstration.
- `README.md`: Centralized mock architectural documentation.

### 4. Mock Services Layer (`src/services/`)
- `mockRepository.ts`: Transactional in-memory repository with local storage persistence (`version: 2`) and cross-entity synchronization.
- `authService.ts`: One-click persona switcher, workspace switching, and simulated authentication.
- `foodService.ts`: Surplus food CRUD and status updates.
- `requestService.ts`: NGO community request management.
- `volunteerService.ts`: Courier tracking and availability status toggles.
- `deliveryService.ts`: Task state-machine progression enforcement.
- `disasterService.ts`: Disaster event lifecycle and operational mode switching.
- `allocationService.ts`: AI recommendations and matching approvals.
- `analyticsService.ts`: Derived metrics and audit trail queries.
- `notificationService.ts`: Read/unread notification state management.

### 5. Verification & Quality Gates
- **TypeScript Strict Mode**: 0 errors (`tsc -b` passed).
- **Linter**: 0 errors, 0 warnings (`oxlint` passed).
- **Vite Production Build**: Built 2,811 modules successfully (`npm run build` passed in 868ms).

---

## Next Steps (Phase 2 & Beyond)
- **Phase 2 — Shared UI & Components**:
  - Full Add Food modal/form with validation and image preview.
  - Dedicated Create Resource Request form.
  - Interactive FilterBar, SearchInput, and DataTable components.
- **Phase 3 — Role Dashboards Deep Dives**:
  - Detailed sub-pages for all 4 roles (Listings, Requests, Dispatches, Approvals).
- **Phase 4 — Intelligent Features UI**:
  - MapLibre GL live map visualization with Moratuwa/Colombo geospatial layers.
  - Apache ECharts integration for donation trends, regional supply/demand balance.
  - Interactive Disaster Mode emergency triage and route disruption re-assignment.
