# Dashboard simplification - Step 1

## Delivered

- Audited the shared shell, role navigation, dashboard routes, Food Provider pages and Django resource organization APIs.
- Wired `/food/listings` to the existing functional `FoodListingsPage` instead of a placeholder.
- Added `/food/allocations` using the existing allocation and pickup tracking page.
- Added a provider-only overview entry that uses the existing provider dashboard while preserving the unified dashboard for multi-role users.
- Added provider-scoped loading and error states to the provider overview.
- Removed the provider overview's hard-coded organization and unsafe global-listing fallback.
- Removed hard-coded provider metadata from the API create workflow.
- Added edit-mode loading and update persistence to the surplus form.
- Preserved legacy `/provider/*` redirects and existing backend workflows.

## Functional Food Provider workflows

| Workflow | Implementation status |
| --- | --- |
| Add surplus food | Wired to `foodService.createListing`; API mode uses authenticated organization membership |
| View listings | Wired to `FoodListingsPage` and `getMyListings` |
| Edit listing | Wired to `foodService.updateListing` for available listings |
| Withdraw listing | Wired to `foodService.withdrawListing` with confirmation |
| View allocations | Wired to `ProviderAllocationsPage` |
| Track pickup | Allocations page pickup tab and handover mutation |
| Profile and logout | Shared profile route and header profile menu |

## Verification

- Frontend production build: `npm run build` was run from `frontend`, but the repository currently fails TypeScript validation in existing live-polling call sites and unused imports outside this step. The provider form's new type error was corrected; remaining failures are listed in the task result.
- Backend tests: `python manage.py test` completed with Django system checks passing but discovered zero tests in the current configuration.
- Browser evidence: requires the local Vite and Django/PostgreSQL services to be started; no deployment or GitHub push was performed.

## Remaining issues

- Donation history remains a placeholder.
- Other role dashboards were intentionally not redesigned in this step.
- Full real-browser login/API/database evidence remains to be captured in an environment with running services.
