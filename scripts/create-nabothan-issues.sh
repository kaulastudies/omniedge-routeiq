#!/usr/bin/env bash
set -euo pipefail

ASSIGNEE="Nabothdaniel"

echo "Creating / updating GitHub labels..."

gh label create "frontend" \
  --color "0EA5E9" \
  --description "Frontend implementation work" \
  --force

gh label create "ui-ux" \
  --color "8B5CF6" \
  --description "User interface and user experience polish" \
  --force

gh label create "demo-ready" \
  --color "22C55E" \
  --description "Required for final demo readiness" \
  --force

gh label create "high-priority" \
  --color "EF4444" \
  --description "High priority for AMD ACT II submission" \
  --force

gh label create "qa" \
  --color "F59E0B" \
  --description "Quality assurance and testing" \
  --force

gh label create "presentation" \
  --color "EC4899" \
  --description "Demo and judge-facing presentation polish" \
  --force

gh label create "frontend-polish" \
  --color "14B8A6" \
  --description "Frontend polish before final submission" \
  --force

mkdir -p /tmp/routeiq-nabothan-issues

cat > /tmp/routeiq-nabothan-issues/01-dashboard-polish.md <<'EOF'
## Goal

Polish the OmniEdge RouteIQ Command Nexus dashboard for the final AMD ACT II Hackathon demo.

## Live Demo

https://omniedge-routeiq.vercel.app

## Scope

Work only inside the frontend:

- `frontend/src/app/page.tsx`
- `frontend/src/app/globals.css`

Please do not change backend logic.

## Tasks

1. Improve spacing, visual hierarchy, and responsive layout.
2. Make metric cards look more premium and easier to scan.
3. Improve the Route Decision panel clarity.
4. Improve Provider Health readability.
5. Make the Audit Timeline more polished and easier to follow.
6. Ensure desktop view looks good at 90% and 100% browser zoom.
7. Keep the design dark-mode, enterprise-grade, and demo-ready.

## Design Direction

Use a polished SaaS dashboard style inspired by:

- Vercel
- Linear
- Stripe
- enterprise observability dashboards

## Naming Rules

Use only these project/team references:

- OmniEdge RouteIQ
- Rama Chandra
- Nabothan
- Rameen
- AMD ACT II Hackathon

Do not use unrelated references such as:

- ClaimSetu
- Stellar
- SCF
- YouTube
- Instagram
- hospital
- patient discharge
- insurance ID
- phone number examples

## Acceptance Criteria

- Dashboard looks polished and demo-ready.
- No broken desktop layout.
- Existing API connection still works.
- No unrelated project text appears.
- `npm run lint` passes.
- `npm run build` passes.
EOF

cat > /tmp/routeiq-nabothan-issues/02-scenario-cards.md <<'EOF'
## Goal

Improve the Built-in Judge Scenarios section so judges immediately understand what each scenario demonstrates.

## Current Scenarios

- `local_sensitive_prompt`
- `cloud_complex_architecture`
- `hybrid_confidential_code`
- `fallback_no_key_demo`

## Tasks

1. Keep scenario IDs visible.
2. Add human-readable titles.
3. Improve preview text readability.
4. Add small route tags if possible:
   - Local
   - Cloud
   - Hybrid
   - Fallback
5. Make the selected or running scenario visually obvious.
6. Keep the section clean, professional, and easy to understand during screen recording.

## Suggested Human Labels

| Scenario ID | Display Label |
|---|---|
| `local_sensitive_prompt` | Privacy-first Local Route |
| `cloud_complex_architecture` | Cloud Architecture Route |
| `hybrid_confidential_code` | Hybrid Confidential Code Route |
| `fallback_no_key_demo` | Fallback Reliability Demo |

## Acceptance Criteria

- Judges can understand each scenario quickly.
- Scenario cards look professional.
- Existing API calls still work.
- No unrelated project text appears.
- `npm run lint` passes.
- `npm run build` passes.
EOF

cat > /tmp/routeiq-nabothan-issues/03-loading-error-states.md <<'EOF'
## Goal

Add clear frontend loading and error feedback so the final demo feels reliable even if the backend is slow.

## Context

The backend is deployed on Render. Render free-tier services may cold start, so the frontend should not look broken if the first request takes a few seconds.

## Tasks

1. Show a visible loading state when `Run Route Decision` is clicked.
2. Show a visible loading state when a scenario card is clicked.
3. Show a clean user-friendly error message if a backend request fails.
4. Add a small backend connection status indicator if possible.
5. Do not show raw stack traces or browser-style error messages to judges.
6. Keep the UI minimal, polished, and professional.

## Acceptance Criteria

- Slow backend response shows a friendly loading state.
- Backend failure shows a clean message.
- Successful routing still updates the dashboard normally.
- `npm run lint` passes.
- `npm run build` passes.
EOF

cat > /tmp/routeiq-nabothan-issues/04-final-frontend-qa.md <<'EOF'
## Goal

Run final frontend QA before demo recording and AMD ACT II Hackathon submission.

## Live Demo

https://omniedge-routeiq.vercel.app

## Backend Wake-Up URL

https://omniedge-routeiq-backend.onrender.com/status

## QA Steps

1. Open the backend status URL and confirm `status: ok`.
2. Open the live frontend dashboard.
3. Click `Refresh Nexus`.
4. Click `Run Route Decision`.
5. Click `local_sensitive_prompt`.
6. Click `cloud_complex_architecture`.
7. Click `hybrid_confidential_code`.
8. Click `fallback_no_key_demo`.
9. Confirm metrics update.
10. Confirm Route Decision updates.
11. Confirm Audit Timeline appears.
12. Confirm Provider Health appears.
13. Confirm Token Savings appears.
14. Confirm no unrelated project text appears.

## Contamination Check

The frontend must not show:

- ClaimSetu
- Stellar
- SCF
- YouTube
- Instagram
- patient discharge
- hospital
- insurance ID
- phone number examples

## Local Build Check

Run:

```bash
cd frontend
npm run lint
npm run build
```

## Acceptance Criteria

- Live dashboard works.
- All demo buttons work.
- Frontend build passes.
- No UI-breaking bugs.
- Any issue is reported with screenshot and exact reproduction steps.
EOF

create_issue_if_missing() {
  local title="$1"
  local body_file="$2"
  shift 2
  local labels=("$@")

  local existing_number
  existing_number="$(gh issue list --state open --search "$title in:title" --json number,title --jq ".[] | select(.title == \"$title\") | .number" | head -n 1)"

  if [[ -n "$existing_number" ]]; then
    echo "Issue already exists: #$existing_number - $title"
    gh issue edit "$existing_number" --add-assignee "$ASSIGNEE" || true

    for label in "${labels[@]}"; do
      gh issue edit "$existing_number" --add-label "$label" || true
    done

    gh issue comment "$existing_number" --body "Updated for final OmniEdge RouteIQ frontend execution. Assigned to Nabothan using GitHub username @$ASSIGNEE. Please work on branch: \`frontend/nabothan-command-nexus-polish\`." || true
  else
    echo "Creating issue: $title"

    label_args=()
    for label in "${labels[@]}"; do
      label_args+=(--label "$label")
    done

    gh issue create \
      --title "$title" \
      --body-file "$body_file" \
      --assignee "$ASSIGNEE" \
      "${label_args[@]}"
  fi
}

echo "Creating / updating Nabothan frontend issues..."

create_issue_if_missing \
  "Polish Command Nexus Dashboard UI for Final Demo" \
  "/tmp/routeiq-nabothan-issues/01-dashboard-polish.md" \
  "frontend" "ui-ux" "demo-ready" "high-priority" "frontend-polish"

create_issue_if_missing \
  "Improve Scenario Cards and Demo Readability" \
  "/tmp/routeiq-nabothan-issues/02-scenario-cards.md" \
  "frontend" "ui-ux" "presentation" "high-priority"

create_issue_if_missing \
  "Add Clear Demo Status and Error Feedback in Frontend" \
  "/tmp/routeiq-nabothan-issues/03-loading-error-states.md" \
  "frontend" "ui-ux" "demo-ready" "frontend-polish"

create_issue_if_missing \
  "Frontend Final QA and Build Check" \
  "/tmp/routeiq-nabothan-issues/04-final-frontend-qa.md" \
  "frontend" "qa" "demo-ready" "high-priority"

echo ""
echo "Completed."
echo ""
echo "Open issues assigned to Nabothan:"
gh issue list --assignee "$ASSIGNEE" --state open
