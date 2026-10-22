# NeighborNet dashboard navigation audit

## Scope

Audited the React router, shared shell, role navigation, Food Provider pages and services, and the Django resources/organizations endpoints. This step intentionally changes only the shared shell composition and Food Provider experience; recipient, volunteer, coordinator and backend workflow implementations remain in place.

## Findings

### Duplicate or unnecessary navigation

- The sidebar and mobile navigation were already separate renderers, but both were fed by role configuration. The configuration was compact enough to retain; the mobile renderer is capped at four destinations.
- Legacy `/provider/*` routes duplicate the newer `/food/*` routes. They are retained as redirects for deep-link compatibility, not shown as navigation.
- Header profile menu is the single logout surface. No additional shell logout control is needed.

### Placeholder and hidden functionality

- `/food/listings` rendered `PlaceholderView`, despite `FoodListingsPage` implementing loading, filtering, edit and withdraw behavior.
- `/food/allocations` had no route, although `ProviderAllocationsPage` implemented allocation and pickup tracking tabs.
- `/food/history` remains a placeholder and is not a primary Food Provider destination.

### Data and integration defects

- `UnifiedDashboard` used a hard-coded `ORG-001` check and fell back to the first five global listings. This could expose another provider's activity in a provider overview.
- `AddFoodPage` sent hard-coded provider metadata. API creation now relies on the authenticated user's organization membership; mock mode still receives the signed-in user's context.
- Provider overview did not expose loading or error states and loaded global listings rather than membership-scoped listings.

## Navigation after Step 1

Food Provider desktop: Overview, My Food, Allocations, Profile.

Food Provider mobile: Overview, My Food, Allocations, Profile.

Secondary actions remain contextual: Add Food from Overview/My Food, edit and withdraw from My Food, and pickup tracking from Allocations.

## Deferred items

- Donation history page implementation.
- Full redesign of recipient, volunteer and coordinator dashboards.
- Browser automation against a running Django/PostgreSQL deployment (requires local services and credentials).
