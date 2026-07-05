#!/usr/bin/env bash
set -euo pipefail

OWNER="$(gh repo view --json owner --jq .owner.login)"
REPO="$(gh repo view --json name --jq .name)"
RAMA_GITHUB="$(gh api user --jq .login)"
NABOTHAN_GITHUB="Nabothdaniel"

# Add Rameen's GitHub username here later if needed.
# If empty, Rameen-owned issues will be labeled but not assigned.
RAMEEN_GITHUB="${RAMEEN_GITHUB:-}"

APPLY="${APPLY:-0}"

echo "Repository: $OWNER/$REPO"
echo "Rama Chandra GitHub: @$RAMA_GITHUB"
echo "Nabothan GitHub: @$NABOTHAN_GITHUB"

if [[ -n "$RAMEEN_GITHUB" ]]; then
  echo "Rameen GitHub: @$RAMEEN_GITHUB"
else
  echo "Rameen GitHub: not set. Rameen issues will be labeled but not assigned."
fi

echo ""
echo "Mode: $([[ "$APPLY" == "1" ]] && echo "APPLY CHANGES" || echo "DRY RUN / REPORT ONLY")"
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

echo "Creating / updating labels..."

create_label "status: done" "22C55E" "Completed work"
create_label "status: todo" "94A3B8" "Ready to start"
create_label "status: in progress" "3B82F6" "Currently being worked on"
create_label "status: needs review" "F59E0B" "Needs founder review"
create_label "status: blocked" "EF4444" "Blocked or waiting on input"
create_label "status: legacy review" "64748B" "Old or imported issue requiring cleanup review"

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
create_label "area: project-board" "6366F1" "GitHub project board organization"

create_label "owner: rama-chandra" "111827" "Owned by Rama Chandra"
create_label "owner: nabothan" "14B8A6" "Owned by Nabothan"
create_label "owner: rameen" "A855F7" "Owned by Rameen"
create_label "owner: unassigned-review" "CBD5E1" "Needs owner confirmation"

create_label "track: amd-act-ii" "000000" "AMD ACT II Hackathon"
create_label "hackathon-ready" "16A34A" "Required for final hackathon readiness"
create_label "demo-ready" "22C55E" "Required for demo readiness"
create_label "legacy-gemini-task" "475569" "Older task created during Gemini planning/import"
create_label "cleanup" "6B7280" "Cleanup or organization task"

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
  else
    gh api -X POST "repos/$OWNER/$REPO/milestones" \
      -f title="$title" \
      -f description="$description" \
      -f due_on="$due_on" >/dev/null
  fi
}

echo "Creating / updating milestones..."

create_milestone \
  "M1 - Foundation Completed" \
  "Completed core build work before final team execution." \
  "2026-07-05T23:59:00Z"

create_milestone \
  "M2 - Team Execution Sprint" \
  "Frontend polish, demo script, QA, and team-owned final improvements." \
  "2026-07-08T23:59:00Z"

create_milestone \
  "M3 - Final Submission Sprint" \
  "Founder-owned final QA, submission content, hybrid routing validation, release snapshot, and final demo package." \
  "2026-07-11T23:59:00Z"

create_milestone \
  "M0 - Legacy Review and Cleanup" \
  "Older Gemini-created or imported issues that need review, cleanup, reassignment, or closure." \
  "2026-07-06T23:59:00Z"

echo "Milestones ready."
echo ""

echo "Fetching all GitHub issues..."

gh issue list \
  --state all \
  --limit 500 \
  --json number,title,body,state,labels,assignees,milestone,createdAt,updatedAt,closedAt,url \
  > .routeiq-audit/issues.json

python3 - <<'PY'
import json
import csv
import re
from pathlib import Path

issues_path = Path(".routeiq-audit/issues.json")
issues = json.loads(issues_path.read_text())

completed_titles = {
    "Lock OmniEdge RouteIQ Project Scope",
    "Initialize OmniEdge RouteIQ Repository Structure",
    "Build FastAPI Backend Routing API",
    "Implement Local Cloud and Fallback Provider Layer",
    "Implement Routing Classifier and Decision Engine",
    "Add Metrics and Audit Trail System",
    "Create Built-in Judge Simulation Scenarios",
    "Clean Old Simulation and Project References",
    "Deploy Backend API on Render",
    "Build Command Nexus Dashboard",
    "Deploy Frontend on Vercel",
    "Polish README and Project Documentation",
    "Create and Assign Rameen Demo and QA Issues",
    "Create and Assign Nabothan Frontend Issues",
}

frontend_keywords = [
    "frontend", "ui", "ux", "dashboard", "command nexus", "scenario card",
    "loading", "error state", "app.tsx", "app.css", "globals.css",
    "component", "responsive", "vercel", "tailwind", "next.js", "nextjs"
]

rameen_keywords = [
    "rameen", "demo script", "video script", "recording", "click-flow",
    "click flow", "submission summary", "qa live demo", "final submission summary",
    "demo video"
]

backend_keywords = [
    "backend", "fastapi", "api", "route", "routing", "classifier",
    "decision engine", "hybrid", "ollama", "fireworks", "provider",
    "mock cloud", "render", "metrics", "audit", "simulation"
]

docs_keywords = [
    "readme", "docs", "documentation", "submission", "portal",
    "summary", "release", "screenshot", "q&a", "judge"
]

deployment_keywords = [
    "deploy", "deployment", "render", "vercel", "production",
    "smoke test", "live", "status"
]

legacy_keywords = [
    "gemini", "old", "claimsetu", "stellar", "scf", "youtube",
    "instagram", "hospital", "patient", "insurance", "phone"
]

p0_keywords = [
    "final", "submission", "demo", "hybrid", "contamination",
    "smoke", "recording", "qa", "portal"
]

def contains_any(text, words):
    text = text.lower()
    return any(w.lower() in text for w in words)

def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()

rows = []

for issue in issues:
    title = issue.get("title") or ""
    body = issue.get("body") or ""
    state = issue.get("state") or ""
    combined = f"{title}\n{body}".lower()

    labels = []
    owner = "unassigned-review"
    assignee_group = ""
    milestone = "M0 - Legacy Review and Cleanup"
    action = "review"
    close_reason = ""

    if title in completed_titles:
        owner = "rama-chandra"
        assignee_group = "rama"
        milestone = "M1 - Foundation Completed"
        labels += ["status: done", "owner: rama-chandra", "track: amd-act-ii", "hackathon-ready", "priority: p0"]
        action = "close"
        close_reason = "completed foundation work"
    else:
        labels += ["track: amd-act-ii"]

        if contains_any(combined, frontend_keywords):
            owner = "nabothan"
            assignee_group = "nabothan"
            milestone = "M2 - Team Execution Sprint"
            labels += ["owner: nabothan", "area: frontend"]
        elif contains_any(combined, rameen_keywords):
            owner = "rameen"
            assignee_group = "rameen"
            milestone = "M2 - Team Execution Sprint"
            labels += ["owner: rameen", "area: demo"]
        elif contains_any(combined, backend_keywords):
            owner = "rama-chandra"
            assignee_group = "rama"
            milestone = "M3 - Final Submission Sprint"
            labels += ["owner: rama-chandra", "area: backend"]
        elif contains_any(combined, docs_keywords):
            owner = "rama-chandra"
            assignee_group = "rama"
            milestone = "M3 - Final Submission Sprint"
            labels += ["owner: rama-chandra", "area: docs"]
        else:
            owner = "unassigned-review"
            assignee_group = ""
            milestone = "M0 - Legacy Review and Cleanup"
            labels += ["owner: unassigned-review", "status: legacy review"]

        if contains_any(combined, backend_keywords) and "area: routing-engine" not in labels:
            if "routing" in combined or "hybrid" in combined or "decision" in combined:
                labels.append("area: routing-engine")

        if contains_any(combined, docs_keywords) and "area: docs" not in labels:
            labels.append("area: docs")

        if contains_any(combined, deployment_keywords) and "area: deployment" not in labels:
            labels.append("area: deployment")

        if "qa" in combined or "test" in combined or "check" in combined:
            labels.append("area: qa")

        if "demo" in combined or "recording" in combined:
            labels.append("area: demo")
            labels.append("demo-ready")

        if "submission" in combined or "portal" in combined:
            labels.append("area: submission")

        if contains_any(combined, legacy_keywords):
            labels += ["legacy-gemini-task", "cleanup", "status: legacy review"]
            milestone = "M0 - Legacy Review and Cleanup"
            if owner == "unassigned-review":
                action = "review"
            else:
                action = "organize"
        else:
            if state.upper() == "CLOSED":
                labels.append("status: done")
                action = "organize"
            else:
                labels.append("status: todo")
                action = "organize"

        if contains_any(combined, p0_keywords):
            labels.append("priority: p0")
            labels.append("hackathon-ready")
        elif owner == "unassigned-review":
            labels.append("priority: p2")
        else:
            labels.append("priority: p1")

    labels = list(dict.fromkeys(labels))

    rows.append({
        "number": issue["number"],
        "title": title,
        "state": state,
        "owner": owner,
        "assignee_group": assignee_group,
        "milestone": milestone,
        "labels": "|".join(labels),
        "action": action,
        "close_reason": close_reason,
        "url": issue.get("url", "")
    })

report_path = Path(".routeiq-audit/issue-audit-report.csv")
with report_path.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "number", "title", "state", "owner", "assignee_group",
            "milestone", "labels", "action", "close_reason", "url"
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

md_path = Path(".routeiq-audit/issue-audit-report.md")
with md_path.open("w") as f:
    f.write("# OmniEdge RouteIQ Issue Audit Report\n\n")
    f.write("This report classifies all GitHub issues into owner, milestone, labels, and recommended action.\n\n")
    f.write("| # | State | Owner | Milestone | Action | Title |\n")
    f.write("|---|---|---|---|---|---|\n")
    for r in rows:
        safe_title = r["title"].replace("|", "\\|")
        f.write(f"| {r['number']} | {r['state']} | {r['owner']} | {r['milestone']} | {r['action']} | {safe_title} |\n")

print(f"Generated {report_path}")
print(f"Generated {md_path}")
PY

echo ""
echo "Audit report created:"
echo ".routeiq-audit/issue-audit-report.md"
echo ".routeiq-audit/issue-audit-report.csv"
echo ""

if [[ "$APPLY" != "1" ]]; then
  echo "Dry run completed. No issues were changed."
  echo ""
  echo "Review the report first:"
  echo "cat .routeiq-audit/issue-audit-report.md"
  echo ""
  echo "To apply organization after review, run:"
  echo "APPLY=1 ./scripts/audit-and-organize-all-issues.sh"
  echo ""
  exit 0
fi

echo "Applying organization to GitHub issues..."

remove_status_labels() {
  local issue="$1"

  gh issue edit "$issue" --remove-label "status: todo" >/dev/null 2>&1 || true
  gh issue edit "$issue" --remove-label "status: in progress" >/dev/null 2>&1 || true
  gh issue edit "$issue" --remove-label "status: needs review" >/dev/null 2>&1 || true
  gh issue edit "$issue" --remove-label "status: blocked" >/dev/null 2>&1 || true
  gh issue edit "$issue" --remove-label "status: done" >/dev/null 2>&1 || true
  gh issue edit "$issue" --remove-label "status: legacy review" >/dev/null 2>&1 || true
}

while IFS=, read -r number title state owner assignee_group milestone labels action close_reason url; do
  if [[ "$number" == "number" ]]; then
    continue
  fi

  echo "Organizing #$number - $title"

  remove_status_labels "$number"

  gh issue edit "$number" --milestone "$milestone" >/dev/null || true

  IFS='|' read -ra label_array <<< "$labels"
  for label in "${label_array[@]}"; do
    if [[ -n "$label" ]]; then
      gh issue edit "$number" --add-label "$label" >/dev/null || true
    fi
  done

  if [[ "$assignee_group" == "rama" ]]; then
    gh issue edit "$number" --add-assignee "$RAMA_GITHUB" >/dev/null || true
  elif [[ "$assignee_group" == "nabothan" ]]; then
    gh issue edit "$number" --add-assignee "$NABOTHAN_GITHUB" >/dev/null || true
  elif [[ "$assignee_group" == "rameen" && -n "$RAMEEN_GITHUB" ]]; then
    gh issue edit "$number" --add-assignee "$RAMEEN_GITHUB" >/dev/null || true
  fi

  if [[ "$action" == "close" ]]; then
    gh issue close "$number" \
      --reason completed \
      --comment "Marked completed during OmniEdge RouteIQ professional dashboard cleanup. Reason: $close_reason." >/dev/null || \
    gh issue close "$number" \
      --comment "Marked completed during OmniEdge RouteIQ professional dashboard cleanup. Reason: $close_reason." >/dev/null || true
  elif [[ "$action" == "review" ]]; then
    gh issue comment "$number" \
      --body "Organized during OmniEdge RouteIQ issue audit. This looks like an older or imported task and needs founder review before closing, rewriting, or assigning." >/dev/null || true
  else
    gh issue comment "$number" \
      --body "Organized during OmniEdge RouteIQ professional issue audit with owner, milestone, and labels." >/dev/null || true
  fi

done < .routeiq-audit/issue-audit-report.csv

echo ""
echo "Issue organization completed."
echo ""

echo "Summary by milestone:"
gh api "repos/$OWNER/$REPO/milestones?state=all&per_page=100" \
  --jq '.[] | "- " + .title + " | open: " + (.open_issues|tostring) + " | closed: " + (.closed_issues|tostring)'

echo ""
echo "Open issues:"
gh issue list --state open --limit 100

echo ""
echo "Useful links:"
echo "Issues:      https://github.com/$OWNER/$REPO/issues"
echo "Milestones:  https://github.com/$OWNER/$REPO/milestones"
echo "Audit file:  .routeiq-audit/issue-audit-report.md"
