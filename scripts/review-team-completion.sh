#!/usr/bin/env bash
set -euo pipefail

OWNER="$(gh repo view --json owner --jq .owner.login)"
REPO="$(gh repo view --json name --jq .name)"
RAMA_GITHUB="$(gh api user --jq .login)"
NABOTHAN_GITHUB="Nabothdaniel"
RAMEEN_GITHUB="r2meen"

echo "Reviewing team issue completion..."
echo "Repo: $OWNER/$REPO"
echo "Founder: @$RAMA_GITHUB"
echo "Nabothan: @$NABOTHAN_GITHUB"
echo "Rameen: @$RAMEEN_GITHUB"
echo ""

mkdir -p .routeiq-audit/team-review

gh issue list \
  --state open \
  --limit 200 \
  --json number,title,body,state,labels,assignees,milestone,url \
  > .routeiq-audit/team-review/open-issues.json

python3 - <<'PY'
import json
import csv
import re
import subprocess
from pathlib import Path

OWNER = subprocess.check_output(["gh", "repo", "view", "--json", "owner", "--jq", ".owner.login"], text=True).strip()
REPO = subprocess.check_output(["gh", "repo", "view", "--json", "name", "--jq", ".name"], text=True).strip()
RAMA = subprocess.check_output(["gh", "api", "user", "--jq", ".login"], text=True).strip()

NABOTHAN = "Nabothdaniel"
RAMEEN = "r2meen"

issues = json.loads(Path(".routeiq-audit/team-review/open-issues.json").read_text())

TEAM_USERS = {NABOTHAN.lower(), RAMEEN.lower()}

COMPLETION_WORDS = [
    "done", "completed", "finished", "ready", "implemented", "fixed",
    "pushed", "opened pr", "created pr", "pull request", "review please",
    "please review", "tested", "verified", "build passed", "lint passed"
]

EVIDENCE_WORDS = [
    "screenshot", "screen shot", "recording", "video", "pr", "pull request",
    "branch", "commit", "npm run lint", "npm run build", "pytest",
    "tested", "verified", "live demo", "checklist", "draft", "script"
]

def run_gh_api(path):
    try:
        out = subprocess.check_output(["gh", "api", path, "--paginate"], text=True)
        if not out.strip():
            return []
        return json.loads(out)
    except Exception:
        return []

def lower_text(value):
    return (value or "").lower()

def contains_any(text, words):
    text = lower_text(text)
    return any(word in text for word in words)

def comments_for_issue(number):
    return run_gh_api(f"repos/{OWNER}/{REPO}/issues/{number}/comments")

def get_team_comments(comments):
    rows = []
    for c in comments:
        author = c.get("user", {}).get("login", "")
        body = c.get("body", "") or ""
        if author.lower() in TEAM_USERS:
            rows.append({
                "author": author,
                "body": body,
                "created_at": c.get("created_at", ""),
                "url": c.get("html_url", "")
            })
    return rows

def get_expected_checks(title):
    t = title.lower()

    if "demo video script" in t:
        return [
            "Mentions demo script or draft",
            "Mentions product story/problem/solution",
            "Mentions route scenarios or screen flow"
        ]

    if "click-flow" in t or "recording checklist" in t:
        return [
            "Mentions recording flow or checklist",
            "Mentions backend/frontend demo steps",
            "Mentions final recording readiness"
        ]

    if "qa live demo" in t or "frontend final qa" in t:
        return [
            "Mentions live demo tested",
            "Mentions scenarios/buttons tested",
            "Mentions errors or no issues found"
        ]

    if "submission summary" in t:
        return [
            "Mentions submission summary/draft",
            "Mentions problem/solution/implementation",
            "Mentions live links or team roles"
        ]

    if "dashboard ui" in t:
        return [
            "Mentions UI polish completed",
            "Mentions frontend-only changes",
            "Mentions lint/build or PR evidence"
        ]

    if "scenario cards" in t:
        return [
            "Mentions scenario labels/cards improved",
            "Mentions local/cloud/hybrid/fallback readability",
            "Mentions lint/build or PR evidence"
        ]

    if "loading" in t or "error feedback" in t:
        return [
            "Mentions loading/error state added",
            "Mentions backend slow/failure handling",
            "Mentions lint/build or PR evidence"
        ]

    return [
        "Mentions task completion",
        "Provides evidence such as PR, screenshot, tests, or checklist",
        "No obvious blocker mentioned"
    ]

def evaluate_issue(issue, team_comments):
    title = issue["title"]
    combined_comments = "\n\n".join(c["body"] for c in team_comments)
    combined_lower = combined_comments.lower()

    expected = get_expected_checks(title)

    completion_claimed = contains_any(combined_comments, COMPLETION_WORDS)
    evidence_present = contains_any(combined_comments, EVIDENCE_WORDS)

    blockers = [
        "blocked", "not able", "cannot", "can't", "issue", "error",
        "failed", "not working", "pending", "waiting"
    ]
    blocker_present = contains_any(combined_comments, blockers)

    met = []
    missing = []

    for check in expected:
        c = check.lower()
        ok = False

        if "script" in c or "draft" in c:
            ok = "script" in combined_lower or "draft" in combined_lower
        elif "story" in c or "problem" in c or "solution" in c:
            ok = any(x in combined_lower for x in ["problem", "solution", "story", "routeiq", "omni"])
        elif "scenario" in c or "buttons" in c:
            ok = any(x in combined_lower for x in ["local", "cloud", "hybrid", "fallback", "scenario", "button"])
        elif "recording" in c or "checklist" in c:
            ok = "recording" in combined_lower or "checklist" in combined_lower or "click-flow" in combined_lower or "click flow" in combined_lower
        elif "live demo" in c:
            ok = "live" in combined_lower or "demo" in combined_lower or "tested" in combined_lower
        elif "submission" in c:
            ok = "submission" in combined_lower or "portal" in combined_lower or "summary" in combined_lower
        elif "links" in c or "team roles" in c:
            ok = "link" in combined_lower or "team" in combined_lower or "role" in combined_lower
        elif "ui polish" in c:
            ok = "ui" in combined_lower or "polish" in combined_lower or "dashboard" in combined_lower
        elif "frontend-only" in c:
            ok = "frontend" in combined_lower or "backend" in combined_lower
        elif "lint" in c or "build" in c or "pr" in c:
            ok = any(x in combined_lower for x in ["npm run lint", "npm run build", "build", "lint", "pr", "pull request"])
        elif "scenario labels" in c or "cards" in c:
            ok = "card" in combined_lower or "label" in combined_lower or "scenario" in combined_lower
        elif "loading" in c or "error state" in c:
            ok = "loading" in combined_lower or "error" in combined_lower
        elif "failure" in c or "slow" in c:
            ok = "slow" in combined_lower or "failure" in combined_lower or "render" in combined_lower or "backend" in combined_lower
        else:
            ok = completion_claimed or evidence_present

        if ok:
            met.append(check)
        else:
            missing.append(check)

    if not team_comments:
        recommendation = "waiting_for_team_update"
    elif blocker_present and not completion_claimed:
        recommendation = "blocked_or_needs_followup"
    elif completion_claimed and evidence_present and len(missing) == 0:
        recommendation = "ready_for_founder_close_review"
    elif completion_claimed and len(missing) <= 1:
        recommendation = "needs_founder_review"
    else:
        recommendation = "needs_more_evidence"

    return {
        "expected": expected,
        "met": met,
        "missing": missing,
        "completion_claimed": completion_claimed,
        "evidence_present": evidence_present,
        "blocker_present": blocker_present,
        "recommendation": recommendation,
        "team_comment_count": len(team_comments)
    }

review_rows = []
md_lines = []

md_lines.append("# OmniEdge RouteIQ Team Completion Review")
md_lines.append("")
md_lines.append("This report checks open team issues assigned to Nabothan and Rameen, reads their comments, and compares completion claims against the issue expectations.")
md_lines.append("")
md_lines.append("| Issue | Assignees | Recommendation | Evidence | Missing | Title |")
md_lines.append("|---|---|---|---|---|---|")

for issue in issues:
    assignees = [a["login"] for a in issue.get("assignees", [])]
    assignee_lowers = {a.lower() for a in assignees}

    is_team_issue = bool(TEAM_USERS.intersection(assignee_lowers))

    if not is_team_issue:
        continue

    comments = comments_for_issue(issue["number"])
    team_comments = get_team_comments(comments)
    evaluation = evaluate_issue(issue, team_comments)

    evidence = []
    if evaluation["completion_claimed"]:
        evidence.append("completion claimed")
    if evaluation["evidence_present"]:
        evidence.append("evidence present")
    if evaluation["blocker_present"]:
        evidence.append("blocker mentioned")
    if not evidence:
        evidence.append("no evidence yet")

    missing_text = "; ".join(evaluation["missing"]) if evaluation["missing"] else "none"

    review_rows.append({
        "number": issue["number"],
        "title": issue["title"],
        "assignees": ", ".join(assignees),
        "team_comment_count": evaluation["team_comment_count"],
        "completion_claimed": evaluation["completion_claimed"],
        "evidence_present": evaluation["evidence_present"],
        "blocker_present": evaluation["blocker_present"],
        "recommendation": evaluation["recommendation"],
        "missing": missing_text,
        "url": issue["url"],
    })

    safe_title = issue["title"].replace("|", "\\|")
    md_lines.append(
        f"| #{issue['number']} | {', '.join(assignees)} | {evaluation['recommendation']} | {', '.join(evidence)} | {missing_text} | {safe_title} |"
    )

    md_lines.append("")
    md_lines.append(f"## #{issue['number']} — {issue['title']}")
    md_lines.append("")
    md_lines.append(f"- URL: {issue['url']}")
    md_lines.append(f"- Assignees: {', '.join(assignees)}")
    md_lines.append(f"- Recommendation: `{evaluation['recommendation']}`")
    md_lines.append(f"- Team comments found: {evaluation['team_comment_count']}")
    md_lines.append("")
    md_lines.append("### Expected Checks")
    for item in evaluation["expected"]:
        mark = "✅" if item in evaluation["met"] else "❌"
        md_lines.append(f"- {mark} {item}")
    md_lines.append("")
    md_lines.append("### Team Comment Evidence")
    if not team_comments:
        md_lines.append("- No completion comment from Nabothan/Rameen yet.")
    else:
        for c in team_comments[-3:]:
            excerpt = re.sub(r"\s+", " ", c["body"]).strip()
            if len(excerpt) > 400:
                excerpt = excerpt[:400] + "..."
            md_lines.append(f"- @{c['author']} at {c['created_at']}: {excerpt}")
    md_lines.append("")

csv_path = Path(".routeiq-audit/team-review/team-completion-review.csv")
with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "number", "title", "assignees", "team_comment_count",
            "completion_claimed", "evidence_present", "blocker_present",
            "recommendation", "missing", "url"
        ],
    )
    writer.writeheader()
    writer.writerows(review_rows)

md_path = Path(".routeiq-audit/team-review/team-completion-review.md")
md_path.write_text("\n".join(md_lines))

close_path = Path(".routeiq-audit/team-review/suggested-close-commands.sh")
with close_path.open("w") as f:
    f.write("#!/usr/bin/env bash\n")
    f.write("set -euo pipefail\n\n")
    f.write("# Review manually before running. These are only suggestions.\n\n")
    for row in review_rows:
        if row["recommendation"] == "ready_for_founder_close_review":
            title = row["title"].replace('"', '\\"')
            f.write(
                f'gh issue close {row["number"]} --reason completed --comment "Founder review completed. Team completion evidence checked against the issue criteria and accepted for: {title}."\n'
            )

close_path.chmod(0o755)

print(f"Generated: {md_path}")
print(f"Generated: {csv_path}")
print(f"Generated: {close_path}")
PY

echo ""
echo "Team completion review generated:"
echo ".routeiq-audit/team-review/team-completion-review.md"
echo ".routeiq-audit/team-review/team-completion-review.csv"
echo ".routeiq-audit/team-review/suggested-close-commands.sh"
echo ""
echo "Read the report with:"
echo "cat .routeiq-audit/team-review/team-completion-review.md"
