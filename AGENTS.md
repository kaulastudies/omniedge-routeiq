# AI Agent Rules

## Scope of Work
- You must **NEVER** touch the `backend/` implementation under any circumstances.
- You must **ONLY** focus on and make changes to the `frontend/` and `frontend-2/` (if applicable) folders.
- Do not modify routing logic, classifiers, endpoints, providers, or core backend models unless explicitly instructed to override this rule.

## Rationale
The backend implementation is considered complete and stable for this stage. All ongoing agent work should focus on UI enhancements, layout improvements, styling updates, and frontend features located strictly within the frontend directories.

## Subpage & UI Design Strictness
- Any new subpages, mobile layouts, or routing layers created in the frontend MUST completely follow the established design tokens and UI shell (`DashboardShell`, `TileCard`, etc.)
- Zero deviations from the existing color palette, icon set, or component layout structure are allowed.
- All functional action properties (like clicks, interactions) must be securely bound to hooks like `useRouteIQ` preserving the current flow structure constraint seamlessly.
