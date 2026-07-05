#!/usr/bin/env bash
set -euo pipefail

RAMA_GITHUB="$(gh api user --jq .login)"
NABOTHAN_GITHUB="Nabothdaniel"
RAMEEN_GITHUB="r2meen"

echo "Final clean OmniEdge RouteIQ issue alignment"
echo "Rama Chandra: @$RAMA_GITHUB"
echo "Nabothan: @$NABOTHAN_GITHUB"
echo "Rameen: @$RAMEEN_GITHUB"
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

echo "Creating clean label set..."

create_label "status: todo" "94A3B8" "Ready to work"
create_label "status: done" "22C55E" "Completed"
create_label "priority: p0" "DC2626" "Critical for final submission"
create_label "priority: p1" "F97316" "Important but not blocking"
create_label "area: backend" "2563EB" "Backend and API work"
create_label "area: frontend" "0EA5E9" "Frontend and dashboard work"
create_label "area: qa" "F59E0B" "Testing and verification"
create_label "area: demo" "EC4899" "Demo and recording work"
create_label "area: docs" "8B5CF6" "Documentation and README work"
create_label "area: deployment" "06B6D4" "Render, Vercel, production checks"
create_label "area: routing-engine" "7C3AED" "Routing classifier and decision engine"
create_label "area: submission" "FB923C" "Hackathon submission package"
create_label "owner: rama-chandra" "111827" "Owned by Rama Chandra"
create_label "owner: nabothan" "14B8A6" "Owned by Nabothan"
create_label "owner: rameen" "A855F7" "Owned by Rameen"
create_label "track: amd-act-ii" "000000" "AMD ACT II Hackathon"

echo "Clean labels ready."
echo ""

NOISY_LABELS=(
  "frontend"
  "backend"
  "qa"
  "demo"
  "documentation"
  "presentation"
  "frontend-polish"
  "ui-ux"
  "high-priority"
  "demo-ready"
  "hackathon-ready"
  "founder-task"
  "routing-engine"
  "submission"
  "deployment"
  "legacy-gemini-task"
  "cleanup"
  "bug-check"
  "status: legacy review"
  "status: in progress"
  "status: needs review"
  "status: blocked"
  "owner: unassigned-review"
  "area: project-board"
)

OWNER_LABELS=(
  "owner: rama-chandra"
  "owner: nabothan"
  "owner: rameen"
)

STATUS_LABELS=(
  "status: todo"
  "status: done"
)

PRIORITY_LABELS=(
  "priority: p0"
  "priority: p1"
  "priority: p2"
)

AREA_LABELS=(
  "area: backend"
  "area: frontend"
  "area: qa"
  "area: demo"
  "area: docs"
  "area: deployment"
  "area: routing-engine"
  "area: submission"
  "area: project-board"
)

remove_label_if_exists() {
  local issue="$1"
  local label="$2"

  gh issue edit "$issue" --remove-label "$label" >/dev/null 2>&1 || true
}

reset_issue_labels() {
  local issue="$1"

  for label in "${NOISY_LABELS[@]}"; do
    remove_label_if_exists "$issue" "$label"
  done

  for label in "${OWNER_LABELS[@]}"; do
    remove_label_if_exists "$issue" "$label"
  done

  for label in "${STATUS_LABELS[@]}"; do
    remove_label_if_exists "$issue" "$label"
  done

  for label in "${PRIORITY_LABELS[@]}"; do
    remove_label_if_exists "$issue" "$label"
  done

  for label in "${AREA_LABELS[@]}"; do
    remove_label_if_exists "$issue" "$label"
  done
}

clear_assignees() {
  local issue="$1"

  gh issue edit "$issue" --remove-assignee "$RAMA_GITHUB" >/dev/null 2>&1 || true
  gh issue edit "$issue" --remove-assignee "$NABOTHAN_GITHUB" >/dev/null 2>&1 || true
  gh issue edit "$issue" --remove-assignee "$RAMEEN_GITHUB" >/dev/null 2>&1 || true
}

add_clean_labels() {
  local issue="$1"
  shift

  for label in "$@"; do
    gh issue edit "$issue" --add-label "$label" >/dev/null 2>&1 || true
  done
}

assign_issue() {
  local issue="$1"
  local assignee="$2"

  gh issue edit "$issue" --add-assignee "$assignee" >/dev/null 2>&1 || true
}

close_completed() {
  local issue="$1"
  local message="$2"

  gh issue close "$issue" \
    --reason completed \
    --comment "$message" >/dev/null 2>&1 || \
  gh issue close "$issue" \
    --comment "$message" >/dev/null 2>&1 || true
}

set_milestone() {
  local issue="$1"
  local milestone="$2"

  gh issue edit "$issue" --milestone "$milestone" >/dev/null 2>&1 || true
}

echo "Resetting labels and assignees for issues #1 to #38..."

for issue in $(seq 1 38); do
  reset_issue_labels "$issue"
  clear_assignees "$issue"
  gh issue edit "$issue" --add-label "track: amd-act-ii" >/dev/null 2>&1 || true
done

echo "Aligning old Gemini issues #1-#4 as completed foundation work..."

for issue in 1 2 3 4; do
  assign_issue "$issue" "$RAMA_GITHUB"
  set_milestone "$issue" "M1 - Foundation Completed"
  add_clean_labels "$issue" \
    "status: done" \
    "owner: rama-chandra" \
    "priority: p0"

  close_completed "$issue" \
    "Closed as completed foundation work for OmniEdge RouteIQ. This was an old Gemini/imported planning issue already covered by the current build."
done

add_clean_labels 1 "area: docs"
add_clean_labels 2 "area: frontend"
add_clean_labels 3 "area: routing-engine"
add_clean_labels 4 "area: qa"

echo "Aligning Rameen issues #5-#8..."

for issue in 5 6 7 8; do
  assign_issue "$issue" "$RAMEEN_GITHUB"
  set_milestone "$issue" "M2 - Team Execution Sprint"
  add_clean_labels "$issue" \
    "status: todo" \
    "owner: rameen" \
    "priority: p0"
done

add_clean_labels 5 "area: demo"
add_clean_labels 6 "area: demo"
add_clean_labels 7 "area: qa"
add_clean_labels 8 "area: submission"

echo "Aligning Nabothan issues #9-#12..."

for issue in 9 10 11 12; do
  assign_issue "$issue" "$NABOTHAN_GITHUB"
  set_milestone "$issue" "M2 - Team Execution Sprint"
  add_clean_labels "$issue" \
    "status: todo" \
    "owner: nabothan" \
    "priority: p0"
done

add_clean_labels 9 "area: frontend"
add_clean_labels 10 "area: frontend"
add_clean_labels 11 "area: frontend"
add_clean_labels 12 "area: qa"

echo "Aligning completed foundation issues #13-#26..."

for issue in $(seq 13 26); do
  assign_issue "$issue" "$RAMA_GITHUB"
  set_milestone "$issue" "M1 - Foundation Completed"
  add_clean_labels "$issue" \
    "status: done" \
    "owner: rama-chandra" \
    "priority: p0"
done

add_clean_labels 13 "area: docs"
add_clean_labels 14 "area: docs"
add_clean_labels 15 "area: backend"
add_clean_labels 16 "area: backend"
add_clean_labels 17 "area: routing-engine"
add_clean_labels 18 "area: backend"
add_clean_labels 19 "area: demo"
add_clean_labels 20 "area: qa"
add_clean_labels 21 "area: deployment"
add_clean_labels 22 "area: frontend"
add_clean_labels 23 "area: deployment"
add_clean_labels 24 "area: docs"
add_clean_labels 25 "area: demo"
add_clean_labels 26 "area: frontend"

echo "Aligning founder final sprint issues #27-#38..."

for issue in $(seq 27 38); do
  assign_issue "$issue" "$RAMA_GITHUB"
  set_milestone "$issue" "M3 - Final Submission Sprint"
  add_clean_labels "$issue" \
    "status: todo" \
    "owner: rama-chandra"
done

add_clean_labels 27 "priority: p0" "area: routing-engine"
add_clean_labels 28 "priority: p0" "area: qa"
add_clean_labels 29 "priority: p0" "area: submission"
add_clean_labels 30 "priority: p0" "area: deployment"
add_clean_labels 31 "priority: p0" "area: demo"
add_clean_labels 32 "priority: p1" "area: deployment"
add_clean_labels 33 "priority: p1" "area: docs"
add_clean_labels 34 "priority: p1" "area: backend"
add_clean_labels 35 "priority: p1" "area: submission"
add_clean_labels 36 "priority: p0" "area: qa"
add_clean_labels 37 "priority: p1" "area: demo"
add_clean_labels 38 "priority: p0" "area: submission"

echo ""
echo "Optional cleanup: removing noisy global labels from repository..."

for label in "${NOISY_LABELS[@]}"; do
  gh label delete "$label" --yes >/dev/null 2>&1 || true
done

gh label delete "priority: p2" --yes >/dev/null 2>&1 || true
gh label delete "area: project-board" --yes >/dev/null 2>&1 || true

echo ""
echo "Final clean alignment completed."
echo ""

echo "Milestone summary:"
OWNER="$(gh repo view --json owner --jq .owner.login)"
REPO="$(gh repo view --json name --jq .name)"

gh api "repos/$OWNER/$REPO/milestones?state=all&per_page=100" \
  --jq '.[] | "- " + .title + " | open: " + (.open_issues|tostring) + " | closed: " + (.closed_issues|tostring)'

echo ""
echo "Rama Chandra open issues:"
gh issue list --assignee "$RAMA_GITHUB" --state open --limit 50

echo ""
echo "Nabothan open issues:"
gh issue list --assignee "$NABOTHAN_GITHUB" --state open --limit 50

echo ""
echo "Rameen open issues:"
gh issue list --assignee "$RAMEEN_GITHUB" --state open --limit 50

echo ""
echo "Remaining M0 legacy issues:"
gh issue list --milestone "M0 - Legacy Review and Cleanup" --state open --limit 50 || true
