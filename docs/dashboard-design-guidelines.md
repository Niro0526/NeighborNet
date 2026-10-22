# NeighborNet dashboard design guidelines

## Shared shell

- Use one `DashboardLayout` and `AppShell` for authenticated pages.
- Keep the desktop sidebar between 200 and 220px when expanded and allow collapse.
- Keep primary role navigation to four or five destinations; make secondary work contextual.
- Use the header for branding, current page title, notifications, profile and logout.
- Use the mobile bottom navigation for at most four destinations and reserve bottom padding in the main content.

## Overview pages

Every overview should provide:

1. A greeting and role or organization context.
2. Two to four values calculated from the active data source.
3. One obvious primary action.
4. A compact recent activity or task list.
5. Explicit loading, empty and error states.

Do not render fallback records from another organization to make a card look populated. In API mode, an API failure is an error state, not mock data.

## Provider workflow

- Add or edit surplus through the Food Provider form.
- Review owned listings in My Food.
- Edit and withdraw only listings that the API permits.
- Review matches and confirm pickup handover in Allocations.
- Refresh after mutations and report server errors near the affected action.

## Responsive behavior

- Avoid fixed-width content that causes horizontal scrolling.
- Prefer `min-w-0`, wrapping controls and full-width mobile actions.
- Keep tables and long activity lists inside an intentional scroll region rather than expanding the page width.
