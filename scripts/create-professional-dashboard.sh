#!/usr/bin/env bash
set -euo pipefail

OWNER="$(gh repo view --json owner --jq .owner.login)"
REPO="$(gh repo view --json name --jq .name)"
ASSIGNEE="$(gh api user --jq .login)"

echo "Repository: $OWNER/$REPO"
echo "Founder assignee detected: @$ASSIGNEE"
echo ""

create_label() {
  local name="$1"
  local color="$2"
  local description="$3"

  gh label create "$name" \
    --color "$color" \
    --description "$description" \
    --force >/dev/null
}

echo "Creating / updating professional labels..."

create_label "status: done" "22C55E" "Completed work"
create_label "status: todo" "94A3B8" "Ready to start"
create_label "status: in progress" "3B82F6" "Currently being worked on"
create_label "status: needs review" "F59E0B" "Needs founder review"
create_label "status: blocked" "EF4444" "Blocked or waiting on input"

create_label "priority: p0" "DC2626" "Critical for final submission"
create_label "priority: p1" "F97316" "Important for demo readiness"
create_label "priority: p2" "EAB308" "Useful polish"

create_label "area: backend" "2563EB" "Backend, API, routing, providers"
create_label "area: frontend" "0EA5E9" "Frontend and dashboard"
create_label "area: docs" "8B5CF6" "README, docs, submission content"
create_label "area: deployment" "06B6D4" "Render, Vercel, production checks"
create_label "area: qa" "F59E0B" "Testing and verification"
create_label "area: demo" "EC4899" "Demo video and recording"
create_label "area: routing-engine" "7C3AED" "Classifier and decision engine"
create_label "area: submission" "FB923C" "Hackathon portal and final package"

create_label "owner: rama-chandra" "111827" "Owned by Rama Chandra"
create_label "owner: nabothan" "14B8A6" "Owned by Nabothan"
create_label "owner: rameen" "A855F7" "Owned by Rameen"

create_label "track: amd-act-ii" "000000" "AMD ACT II Hackathon"
create_label "hackathon-ready" "16A34A" "Required for final hackathon readiness"
create_label "demo-ready" "22C55E" "Required for demo readiness"

echo "Labels ready."
echo ""

create_milestone() {
  local title="$1"
  local description="$2"
  local due_on="$3"

  local existing
  existing="$(gh api "repos/$OWNER/$REPO/milestones?state=all&per_page=100" \
    --jq ".[] | select(.title == \"$title\") | .number" | head -n 1)"

  if [[ -n "$existing" ]]; then
    gh api -X PATCH "repos/$OWNER/$REPO/milestones/$existing" \
      -f title="$title" \
      -f description="$description" \
      -f due_on="$due_on" \
      -f state="open" >/dev/null
    echo "Milestone updated: $title"
  else
    gh api -X POST "repos/$OWNER/$REPO/milestones" \
      -f title="$title" \
      -f description="$description" \
      -f due_on="$due_on" >/dev/null
    echo "Milestone created: $title"
  fi
}

echo "Creating / updating milestones..."

create_milestone \
  "M1 - Foundation Completed" \
  "Completed core build work before final team execution: repo, backend, frontend, deployment, README, simulations, and team task setup." \
  "2026-07-05T23:59:00Z"

create_milestone \
  "M2 - Team Execution Sprint" \
  "Frontend polish, demo script, QA, recording flow, and team-owned final improvements." \
  "2026-07-08T23:59:00Z"

create_milestone \
  "M3 - Final Submission Sprint" \
  "Founder-owned final QA, submission content, hybrid routing validation, release snapshot, and final demo package." \
  "2026-07-11T23:59:00Z"

echo ""

get_issue_number() {
  local title="$1"

  gh issue list \
    --state all \
    --limit 200 \
    --search "$title in:title" \
    --json number,title \
    --jq ".[] | select(.title == \"$title\") | .number" | head -n 1
}

add_labels_to_issue() {
  local issue_number="$1"
  shift

  for label in "$@"; do
    gh issue edit "$issue_number" --add-label "$label" >/dev/null || true
  done
}

create_or_update_issue() {
  local title="$1"
  local body_file="$2"
  local milestone="$3"
  local state="$4"
  shift 4
  local labels=("$@")

  local issue_number
  issue_number="$(get_issue_number "$title")"

  if [[ -n "$issue_number" ]]; then
    echo "Updating issue #$issue_number: $title"

    gh issue edit "$issue_number" \
      --add-assignee "$ASSIGNEE" \
      --milestone "$milestone" >/dev/null || true

    add_labels_to_issue "$issue_number" "${labels[@]}"

    if [[ "$state" == "closed" ]]; then
      gh issue close "$issue_number" \
        --reason completed \
        --comment "Marked completed as part of the OmniEdge RouteIQ foundation execution dashboard." >/dev/null || \
      gh issue close "$issue_number" \
        --comment "Marked completed as part of the OmniEdge RouteIQ foundation execution dashboard." >/dev/null || true
    fi
  else
    echo "Creating issue: $title"

    local label_args=()
    for label in "${labels[@]}"; do
      label_args+=(--label "$label")
    done

    issue_url="$(gh issue create \
      --title "$title" \
      --body-file "$body_file" \
      --assignee "$ASSIGNEE" \
      --milestone "$milestone" \
      "${label_args[@]}")"

    issue_number="${issue_url##*/}"

    if [[ "$state" == "closed" ]]; then
      gh issue close "$issue_number" \
        --reason completed \
        --comment "Marked completed as part of the OmniEdge RouteIQ foundation execution dashboard." >/dev/null || \
      gh issue close "$issue_number" \
        --comment "Marked completed as part of the OmniEdge RouteIQ foundation execution dashboard." >/dev/null || true
    fi
  fi
}

mkdir -p /tmp/routeiq-dashboard/completed
mkdir -p /tmp/routeiq-dashboard/open

write_completed_issue() {
  local file="$1"
  local title="$2"
  local summary="$3"

  cat > "$file" <<EOF
## Status

Completed.

## Summary

$summary

## Project

OmniEdge RouteIQ

## Track

AMD ACT II Hackathon

## Owner

Rama Chandra

## Completion Notes

This task was completed before the final team execution sprint and is being added to GitHub Issues for professional tracking, milestone visibility, and project history.
EOF
}

write_open_issue() {
  local file="$1"
  local title="$2"
  local goal="$3"
  local tasks="$4"
  local acceptance="$5"

  cat > "$file" <<EOF
## Owner

Rama Chandra

## Goal

$goal

## Tasks

$tasks

## Acceptance Criteria

$acceptance

## Project Rules

Use only these references:

- OmniEdge RouteIQ
- Rama Chandra
- Nabothan
- Rameen
- AMD ACT II Hackathon

Do not include unrelated references such as ClaimSetu, Stellar, SCF, YouTube, Instagram, hospital, patient discharge, insurance ID, or phone number examples.
EOF
}

write_completed_issue "/tmp/routeiq-dashboard/completed/01-scope.md" \
  "Lock OmniEdge RouteIQ Project Scope" \
  "Locked the project direction as OmniEdge RouteIQ, focused on token-efficient AI agent routing for AMD ACT II."

write_completed_issue "/tmp/routeiq-dashboard/completed/02-repo.md" \
  "Initialize OmniEdge RouteIQ Repository Structure" \
  "Created and organized the GitHub repository structure for frontend, backend, docs, deployment files, and project execution."

write_completed_issue "/tmp/routeiq-dashboard/completed/03-backend.md" \
  "Build FastAPI Backend Routing API" \
  "Implemented the backend API foundation with FastAPI, route endpoints, status endpoint, metrics endpoint, simulation endpoint, and audit endpoint."

write_completed_issue "/tmp/routeiq-dashboard/completed/04-providers.md" \
  "Implement Local Cloud and Fallback Provider Layer" \
  "Added provider abstraction for Ollama local inference, Fireworks cloud inference, and mock cloud fallback for reliable demo execution."

write_completed_issue "/tmp/routeiq-dashboard/completed/05-decision-engine.md" \
  "Implement Routing Classifier and Decision Engine" \
  "Built the routing classifier and decision engine to score privacy, complexity, latency, token cost, and provider availability."

write_completed_issue "/tmp/routeiq-dashboard/completed/06-metrics-audit.md" \
  "Add Metrics and Audit Trail System" \
  "Implemented metrics tracking and explainable audit timeline so each routing decision can be inspected clearly."

write_completed_issue "/tmp/routeiq-dashboard/completed/07-simulations.md" \
  "Create Built-in Judge Simulation Scenarios" \
  "Created simulation scenarios for local, cloud, hybrid, and fallback demo flows."

write_completed_issue "/tmp/routeiq-dashboard/completed/08-cleanup.md" \
  "Clean Old Simulation and Project References" \
  "Removed unrelated sample text and old project references from simulation content to keep OmniEdge RouteIQ clean."

write_completed_issue "/tmp/routeiq-dashboard/completed/09-render.md" \
  "Deploy Backend API on Render" \
  "Deployed the FastAPI backend to Render and verified live status, CORS, and production configuration."

write_completed_issue "/tmp/routeiq-dashboard/completed/10-frontend.md" \
  "Build Command Nexus Dashboard" \
  "Built the Next.js Command Nexus dashboard with route decisions, metrics, provider health, simulations, and audit timeline."

write_completed_issue "/tmp/routeiq-dashboard/completed/11-vercel.md" \
  "Deploy Frontend on Vercel" \
  "Deployed the live frontend dashboard to Vercel and connected it to the Render backend."

write_completed_issue "/tmp/routeiq-dashboard/completed/12-readme.md" \
  "Polish README and Project Documentation" \
  "Added professional README content, architecture notes, judging alignment, demo guidance, and submission-focused documentation."

write_completed_issue "/tmp/routeiq-dashboard/completed/13-rameen.md" \
  "Create and Assign Rameen Demo and QA Issues" \
  "Created focused issues for Rameen covering demo script, recording flow, QA, and submission story."

write_completed_issue "/tmp/routeiq-dashboard/completed/14-nabothan.md" \
  "Create and Assign Nabothan Frontend Issues" \
  "Created focused issues for Nabothan covering dashboard polish, scenario readability, loading states, and frontend QA."

write_open_issue "/tmp/routeiq-dashboard/open/01-hybrid.md" \
  "Finalize Hybrid Routing Demonstration" \
  "Ensure OmniEdge RouteIQ visibly demonstrates local, cloud, hybrid, and fallback routing before final submission." \
  "1. Verify hybrid_confidential_code returns HYBRID.
2. Patch decision engine if needed.
3. Add or update backend test for hybrid route.
4. Run backend tests.
5. Redeploy backend if changed.
6. Confirm frontend displays HYBRID clearly." \
  "- Hybrid route is visible in live demo.
- Backend tests pass.
- Live dashboard reflects the decision correctly."

write_open_issue "/tmp/routeiq-dashboard/open/02-contamination.md" \
  "Run Final Contamination Check Across Repo" \
  "Run a final cleanup check so no unrelated project names or old examples appear in repo, docs, backend, or frontend." \
  "1. Run repository grep for unrelated terms.
2. Remove any unwanted references.
3. Re-run grep until clean.
4. Commit cleanup if needed.
5. Confirm live frontend is clean." \
  "- No unrelated text appears.
- README, docs, backend simulations, and frontend are clean."

write_open_issue "/tmp/routeiq-dashboard/open/03-submission.md" \
  "Prepare Final Hackathon Submission Content" \
  "Prepare final AMD ACT II submission copy for the hackathon portal." \
  "1. Finalize short description.
2. Finalize problem statement.
3. Finalize solution explanation.
4. Finalize technical implementation.
5. Finalize impact and innovation.
6. Add team roles.
7. Verify all live links." \
  "- Submission text is ready.
- Links are correct.
- Story is clear and judge-friendly."

write_open_issue "/tmp/routeiq-dashboard/open/04-smoke-test.md" \
  "Run Live Deployment Smoke Test" \
  "Verify the live Render backend and Vercel frontend work before final recording." \
  "1. Open backend status URL.
2. Open frontend dashboard.
3. Click Refresh Nexus.
4. Run default route decision.
5. Run all built-in scenarios.
6. Confirm metrics, audit trail, token savings, and provider health update." \
  "- Live app works.
- All demo buttons work.
- No visible errors.
- Product is ready for recording."

write_open_issue "/tmp/routeiq-dashboard/open/05-demo-review.md" \
  "Review Final Demo Recording and Submission Package" \
  "Review the final demo video and full submission package before hackathon submission." \
  "1. Review video clarity.
2. Confirm product value is clear in first 30 seconds.
3. Confirm dashboard is visible.
4. Confirm live product is shown.
5. Confirm no unrelated projects are mentioned.
6. Approve final package." \
  "- Demo video is professional.
- Final submission package is ready."

write_open_issue "/tmp/routeiq-dashboard/open/06-release.md" \
  "Create Final Release Tag and Submission Snapshot" \
  "Create a clean final GitHub release/tag for the hackathon submission." \
  "1. Ensure main branch is clean.
2. Confirm README links.
3. Confirm docs are updated.
4. Create final release tag.
5. Add release notes summarizing the product." \
  "- Final release tag exists.
- Repo snapshot is submission-ready."

write_open_issue "/tmp/routeiq-dashboard/open/07-screenshots.md" \
  "Add Final Screenshots to Documentation" \
  "Add final dashboard screenshots or assets to make the GitHub repo more judge-friendly." \
  "1. Capture dashboard screenshot.
2. Add image to docs/assets.
3. Reference screenshot in README if useful.
4. Ensure image does not show unrelated text." \
  "- README/docs look more visual.
- Screenshot is clean and professional."

write_open_issue "/tmp/routeiq-dashboard/open/08-api-examples.md" \
  "Verify API Docs and Endpoint Examples" \
  "Verify backend API docs and curl examples are accurate before submission." \
  "1. Open backend API docs.
2. Test /status.
3. Test /simulations.
4. Test /metrics.
5. Test /route with a clean sample prompt.
6. Update README examples if needed." \
  "- API docs work.
- Example commands are correct."

write_open_issue "/tmp/routeiq-dashboard/open/09-judge-qa.md" \
  "Prepare Judge Q&A and Technical Defense Notes" \
  "Prepare strong answers for likely judge questions about architecture, token savings, privacy, fallback, and AMD relevance." \
  "1. Prepare answer for why this is not just a chatbot.
2. Prepare answer for token efficiency.
3. Prepare answer for privacy.
4. Prepare answer for fallback reliability.
5. Prepare answer for future AMD integration.
6. Prepare answer for enterprise use cases." \
  "- Judge Q&A notes are ready.
- Founder can explain product confidently."

write_open_issue "/tmp/routeiq-dashboard/open/10-pr-review.md" \
  "Review Team PRs and Protect Main Branch Quality" \
  "Review Nabothan and Rameen contributions before merging final changes." \
  "1. Review changed files.
2. Confirm no backend contract breaks.
3. Confirm no unrelated references.
4. Confirm lint/build outputs.
5. Merge only clean PRs.
6. Retest live app after merge." \
  "- Only clean PRs are merged.
- Main branch remains submission-ready."

write_open_issue "/tmp/routeiq-dashboard/open/11-token-story.md" \
  "Validate Token Savings Story for Demo" \
  "Make sure token savings and routing efficiency are clearly shown in the demo." \
  "1. Review metrics dashboard.
2. Confirm token savings display is visible.
3. Prepare one-line explanation for judges.
4. Connect savings to local-first routing and fallback logic." \
  "- Token efficiency story is clear.
- Dashboard supports the narrative."

write_open_issue "/tmp/routeiq-dashboard/open/12-final-checklist.md" \
  "Complete Final Portal Submission Checklist" \
  "Complete the final before-submit checklist for AMD ACT II." \
  "1. GitHub repo link ready.
2. Live demo link ready.
3. Backend docs link ready.
4. Demo video ready.
5. Submission text ready.
6. Team names consistent.
7. No unrelated project references.
8. Final smoke test passed." \
  "- Portal-ready package is complete.
- Submission can be confidently sent."

echo ""
echo "Creating completed foundation issues..."

create_or_update_issue \
  "Lock OmniEdge RouteIQ Project Scope" \
  "/tmp/routeiq-dashboard/completed/01-scope.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: docs"

create_or_update_issue \
  "Initialize OmniEdge RouteIQ Repository Structure" \
  "/tmp/routeiq-dashboard/completed/02-repo.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: docs"

create_or_update_issue \
  "Build FastAPI Backend Routing API" \
  "/tmp/routeiq-dashboard/completed/03-backend.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: backend"

create_or_update_issue \
  "Implement Local Cloud and Fallback Provider Layer" \
  "/tmp/routeiq-dashboard/completed/04-providers.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: backend"

create_or_update_issue \
  "Implement Routing Classifier and Decision Engine" \
  "/tmp/routeiq-dashboard/completed/05-decision-engine.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: routing-engine"

create_or_update_issue \
  "Add Metrics and Audit Trail System" \
  "/tmp/routeiq-dashboard/completed/06-metrics-audit.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: backend" "area: qa"

create_or_update_issue \
  "Create Built-in Judge Simulation Scenarios" \
  "/tmp/routeiq-dashboard/completed/07-simulations.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: demo" "area: backend"

create_or_update_issue \
  "Clean Old Simulation and Project References" \
  "/tmp/routeiq-dashboard/completed/08-cleanup.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: qa"

create_or_update_issue \
  "Deploy Backend API on Render" \
  "/tmp/routeiq-dashboard/completed/09-render.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: deployment" "area: backend"

create_or_update_issue \
  "Build Command Nexus Dashboard" \
  "/tmp/routeiq-dashboard/completed/10-frontend.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: frontend"

create_or_update_issue \
  "Deploy Frontend on Vercel" \
  "/tmp/routeiq-dashboard/completed/11-vercel.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: deployment" "area: frontend"

create_or_update_issue \
  "Polish README and Project Documentation" \
  "/tmp/routeiq-dashboard/completed/12-readme.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: docs"

create_or_update_issue \
  "Create and Assign Rameen Demo and QA Issues" \
  "/tmp/routeiq-dashboard/completed/13-rameen.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "owner: rameen" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: demo" "area: qa"

create_or_update_issue \
  "Create and Assign Nabothan Frontend Issues" \
  "/tmp/routeiq-dashboard/completed/14-nabothan.md" \
  "M1 - Foundation Completed" \
  "closed" \
  "status: done" "owner: rama-chandra" "owner: nabothan" "track: amd-act-ii" "hackathon-ready" "priority: p0" "area: frontend"

echo ""
echo "Creating / updating open founder execution issues..."

create_or_update_issue \
  "Finalize Hybrid Routing Demonstration" \
  "/tmp/routeiq-dashboard/open/01-hybrid.md" \
  "M3 - Final Submission Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p0" "hackathon-ready" "demo-ready" "area: backend" "area: routing-engine"

create_or_update_issue \
  "Run Final Contamination Check Across Repo" \
  "/tmp/routeiq-dashboard/open/02-contamination.md" \
  "M3 - Final Submission Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p0" "hackathon-ready" "demo-ready" "area: qa"

create_or_update_issue \
  "Prepare Final Hackathon Submission Content" \
  "/tmp/routeiq-dashboard/open/03-submission.md" \
  "M3 - Final Submission Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p0" "hackathon-ready" "area: submission" "area: docs"

create_or_update_issue \
  "Run Live Deployment Smoke Test" \
  "/tmp/routeiq-dashboard/open/04-smoke-test.md" \
  "M3 - Final Submission Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p0" "hackathon-ready" "demo-ready" "area: deployment" "area: qa"

create_or_update_issue \
  "Review Final Demo Recording and Submission Package" \
  "/tmp/routeiq-dashboard/open/05-demo-review.md" \
  "M3 - Final Submission Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p0" "hackathon-ready" "demo-ready" "area: demo" "area: submission"

create_or_update_issue \
  "Create Final Release Tag and Submission Snapshot" \
  "/tmp/routeiq-dashboard/open/06-release.md" \
  "M3 - Final Submission Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p1" "hackathon-ready" "area: deployment" "area: docs"

create_or_update_issue \
  "Add Final Screenshots to Documentation" \
  "/tmp/routeiq-dashboard/open/07-screenshots.md" \
  "M3 - Final Submission Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p1" "hackathon-ready" "area: docs" "area: frontend"

create_or_update_issue \
  "Verify API Docs and Endpoint Examples" \
  "/tmp/routeiq-dashboard/open/08-api-examples.md" \
  "M3 - Final Submission Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p1" "hackathon-ready" "area: backend" "area: docs"

create_or_update_issue \
  "Prepare Judge Q&A and Technical Defense Notes" \
  "/tmp/routeiq-dashboard/open/09-judge-qa.md" \
  "M3 - Final Submission Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p1" "hackathon-ready" "area: submission" "area: demo"

create_or_update_issue \
  "Review Team PRs and Protect Main Branch Quality" \
  "/tmp/routeiq-dashboard/open/10-pr-review.md" \
  "M2 - Team Execution Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p0" "hackathon-ready" "area: qa"

create_or_update_issue \
  "Validate Token Savings Story for Demo" \
  "/tmp/routeiq-dashboard/open/11-token-story.md" \
  "M3 - Final Submission Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p1" "hackathon-ready" "demo-ready" "area: demo" "area: routing-engine"

create_or_update_issue \
  "Complete Final Portal Submission Checklist" \
  "/tmp/routeiq-dashboard/open/12-final-checklist.md" \
  "M3 - Final Submission Sprint" \
  "open" \
  "status: todo" "owner: rama-chandra" "track: amd-act-ii" "priority: p0" "hackathon-ready" "area: submission" "area: qa"

tag_existing_issue() {
  local title="$1"
  local milestone="$2"
  shift 2
  local labels=("$@")

  local issue_number
  issue_number="$(get_issue_number "$title")"

  if [[ -n "$issue_number" ]]; then
    echo "Organizing existing issue #$issue_number: $title"

    gh issue edit "$issue_number" --milestone "$milestone" >/dev/null || true
    add_labels_to_issue "$issue_number" "${labels[@]}"
  else
    echo "Existing issue not found, skipping: $title"
  fi
}

echo ""
echo "Organizing existing Nabothan and Rameen team issues if present..."

tag_existing_issue \
  "Polish Command Nexus Dashboard UI for Final Demo" \
  "M2 - Team Execution Sprint" \
  "status: todo" "owner: nabothan" "track: amd-act-ii" "priority: p0" "area: frontend" "demo-ready"

tag_existing_issue \
  "Improve Scenario Cards and Demo Readability" \
  "M2 - Team Execution Sprint" \
  "status: todo" "owner: nabothan" "track: amd-act-ii" "priority: p1" "area: frontend" "area: demo"

tag_existing_issue \
  "Add Clear Demo Status and Error Feedback in Frontend" \
  "M2 - Team Execution Sprint" \
  "status: todo" "owner: nabothan" "track: amd-act-ii" "priority: p1" "area: frontend" "area: qa"

tag_existing_issue \
  "Frontend Final QA and Build Check" \
  "M2 - Team Execution Sprint" \
  "status: todo" "owner: nabothan" "track: amd-act-ii" "priority: p0" "area: frontend" "area: qa" "demo-ready"

tag_existing_issue \
  "Prepare Final Demo Video Script for OmniEdge RouteIQ" \
  "M2 - Team Execution Sprint" \
  "status: todo" "owner: rameen" "track: amd-act-ii" "priority: p0" "area: demo" "demo-ready"

tag_existing_issue \
  "Create Demo Video Click-Flow and Recording Checklist" \
  "M2 - Team Execution Sprint" \
  "status: todo" "owner: rameen" "track: amd-act-ii" "priority: p0" "area: demo" "area: qa" "demo-ready"

tag_existing_issue \
  "QA Live Demo Before Final Recording" \
  "M2 - Team Execution Sprint" \
  "status: todo" "owner: rameen" "track: amd-act-ii" "priority: p0" "area: qa" "demo-ready"

tag_existing_issue \
  "Prepare Final Submission Summary for Hackathon Portal" \
  "M2 - Team Execution Sprint" \
  "status: todo" "owner: rameen" "track: amd-act-ii" "priority: p1" "area: submission" "area: docs"

echo ""
echo "Dashboard setup completed."
echo ""
echo "Milestones:"
gh api "repos/$OWNER/$REPO/milestones?state=all&per_page=100" \
  --jq '.[] | "- " + .title + " | open: " + (.open_issues|tostring) + " | closed: " + (.closed_issues|tostring)'

echo ""
echo "Open issues assigned to you:"
gh issue list --assignee "$ASSIGNEE" --state open --limit 50

echo ""
echo "Completed issues assigned to you:"
gh issue list --assignee "$ASSIGNEE" --state closed --limit 30

echo ""
echo "Useful dashboard links:"
echo "Issues:     https://github.com/$OWNER/$REPO/issues"
echo "Milestones: https://github.com/$OWNER/$REPO/milestones"
echo "Your work:  https://github.com/$OWNER/$REPO/issues?q=is%3Aissue+assignee%3A$ASSIGNEE"
