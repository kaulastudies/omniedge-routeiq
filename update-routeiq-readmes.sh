#!/usr/bin/env bash
set -Eeuo pipefail

# OmniEdge RouteIQ README updater
#
# Run from the repository root:
#   chmod +x update-routeiq-readmes.sh
#   ./update-routeiq-readmes.sh
#
# Optional automatic commit:
#   AUTO_COMMIT=1 ./update-routeiq-readmes.sh
#
# Optional automatic commit and push:
#   AUTO_COMMIT=1 AUTO_PUSH=1 ./update-routeiq-readmes.sh

AUTO_COMMIT="${AUTO_COMMIT:-0}"
AUTO_PUSH="${AUTO_PUSH:-0}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR=".routeiq-readme-backup-${STAMP}"

fail() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail "git is required"
command -v python3 >/dev/null 2>&1 || fail "python3 is required"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || \
  fail "Run this script from inside the OmniEdge RouteIQ repository."

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

[[ -f README.md ]] || fail "README.md was not found at the repository root."

mkdir -p "$BACKUP_DIR"

backup_file() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  mkdir -p "$BACKUP_DIR/$(dirname "$file")"
  cp "$file" "$BACKUP_DIR/$file"
}

backup_file README.md
backup_file docs/README.md
backup_file docs/TEAM_OWNERSHIP.md
backup_file docs/HACKATHON_RESULT.md

while IFS= read -r file; do
  backup_file "$file"
done < <(
  find . -maxdepth 3 -type f -name README.md \
    \( -path './track1-*/*' -o -path './track1*/*' \) \
    -print | sed 's#^\./##' | sort -u
)

mkdir -p docs

cat > README.md <<'MARKDOWN'
<p align="center">
  <img src="docs/assets/routeiq-mark.svg" alt="OmniEdge RouteIQ mark" width="110" />
</p>

# OmniEdge RouteIQ

**A local-first AI routing control plane for token efficiency, privacy-aware execution, cloud escalation, fallback reliability, and explainable audit trails.**

[Live Demo](https://omniedge-routeiq.vercel.app) ·
[API Docs](https://omniedge-routeiq-backend.onrender.com/docs) ·
[Backend Status](https://omniedge-routeiq-backend.onrender.com/status)

---

## AMD ACT II — Final Observed Track 1 Result

The final qualified leaderboard snapshot observed near the close of the AMD Developer Hackathon: ACT II was:

| Metric | Final observed result |
|---|---:|
| Track | Hybrid Token-Efficient Routing Agent |
| Leaderboard position | **17th** |
| Accuracy | **94.7%** |
| Fireworks tokens | **3,100** |
| Qualified tasks | **18 of 19** |
| Initial qualified baseline | 12,531 tokens at 84.2% accuracy |
| Token reduction from initial baseline | **75.3%** |
| Status | Qualified, scored, and preserved |

The team stopped further high-risk experiments during the closing hours to protect the qualified score and avoid losing the position through regressions, schema errors, timeouts, or infrastructure failures.

> This is the final leaderboard result observed by the team. Prize decisions, manual reviews, or organizer-side adjustments may be reported separately.

### Benchmark progression

| Stage | Accuracy | Fireworks tokens | Outcome |
|---|---:|---:|---|
| Early qualified run | 84.2% | 12,531 | Established a valid scoring baseline |
| Major optimization | 94.7% | 3,974 | Reached the top 10 in an earlier snapshot |
| Local-first experiment | 89.5% | 3,421 | Lower token use, but accuracy regressed |
| Final preserved run | **94.7%** | **3,100** | Finished at the observed **17th position** |

### Final experimental learning

A separate v1.8.1 single-pass local candidate completed an internal 19-task benchmark using deterministic solvers and local inference without Fireworks calls. It reached 18 of 19 locally, but the team did not treat it as the final protected submission because one incorrect answer could have reduced the official score.

This experiment remains useful research for future zero-token routing work.

---

## What RouteIQ Does

Most AI applications send every request to the same cloud model. RouteIQ places a routing layer between the application and the inference providers.

For each request, it considers:

- privacy sensitivity;
- task type and complexity;
- local solver confidence;
- latency constraints;
- estimated token cost;
- provider availability;
- fallback reliability;
- required output format.

It then selects an execution path and records the decision.

```text
Application request
        ↓
Task and policy analysis
        ↓
Deterministic local solver
        ↓
Local model when suitable
        ↓
Approved cloud model only when required
        ↓
Validation and answer normalization
        ↓
Result + metrics + explainable audit trail
```

The product principle is simple:

> Do not send every prompt to the cloud by default. Route it intelligently.

---

## Two Working Layers

### 1. Track 1 scoring agent

The containerized benchmark agent follows the official evaluator contract:

```text
Input:  /input/tasks.json
Output: /output/results.json
```

The agent:

- reads all supplied tasks;
- preserves each `task_id`;
- uses deterministic local solvers where confidence is high;
- uses local inference for selected unresolved tasks;
- escalates only when needed and permitted;
- writes benchmark-compatible JSON;
- targets `linux/amd64`;
- respects evaluator-provided model and environment constraints.

### 2. Command Nexus product dashboard

The product layer demonstrates how the routing engine can be used in practical enterprise systems.

It includes:

- route decision visibility;
- local, cloud, hybrid, and fallback paths;
- token savings indicators;
- latency metrics;
- provider health;
- simulation scenarios;
- consent and audit concepts;
- an explainable event timeline.

---

## Core Features

- Local-first execution for supported tasks
- Deterministic arithmetic, sentiment, logic, code, NER, and summary handling
- Local model inference for selected unresolved tasks
- Controlled Fireworks AI fallback
- Strict output validation and normalization
- Token-use reduction
- Privacy-aware route selection
- Provider fallback handling
- Metrics and audit trail
- Dockerized evaluator adapter
- Public Next.js dashboard and FastAPI backend

---

## Product Architecture

```text
User or application
        ↓
Next.js Command Nexus dashboard
        ↓
FastAPI routing API
        ↓
Routing classifier and policy engine
        ↓
Provider registry
   ┌────┼─────────────┐
   ↓    ↓             ↓
Local  Cloud        Fallback
   └────┼─────────────┘
        ↓
Normalized response
        ↓
Metrics + audit timeline
        ↓
Dashboard visualization
```

### Route types

| Route | Purpose |
|---|---|
| Local | Sensitive, simple, or deterministic tasks suitable for local execution |
| Cloud | Complex public tasks requiring stronger remote inference |
| Hybrid | Privacy-aware processing with controlled escalation |
| Fallback | Recovery when a preferred provider is unavailable |

---

## Live Links

| Layer | Link |
|---|---|
| Frontend demo | https://omniedge-routeiq.vercel.app |
| Backend API documentation | https://omniedge-routeiq-backend.onrender.com/docs |
| Backend health check | https://omniedge-routeiq-backend.onrender.com/status |
| Source repository | https://github.com/kaulastudies/omniedge-routeiq |

---

## API Endpoints

```text
GET  /status
GET  /metrics
GET  /simulations
POST /simulations/{scenario_id}
POST /route
GET  /audit/recent
```

Example:

```bash
curl -X POST \
  https://omniedge-routeiq-backend.onrender.com/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Summarize this confidential enterprise incident report and identify risks.",
    "task_type": "summarization",
    "privacy_level": "confidential",
    "max_latency_ms": 2000,
    "prefer_local": true
  }'
```

---

## Demo Scenarios

| Scenario | Demonstrates |
|---|---|
| `local_sensitive_prompt` | Privacy-aware local-first routing |
| `cloud_complex_architecture` | Cloud-capable reasoning |
| `hybrid_confidential_code` | Hybrid handling for confidential code |
| `fallback_no_key_demo` | Recovery when a cloud key or provider is unavailable |

---

## Tech Stack

### Scoring agent

- Python
- Deterministic local solvers
- Local Qwen inference experiments
- Fireworks AI fallback
- Docker
- GitHub Actions
- GHCR
- Linux AMD64 packaging

### Product backend

- Python
- FastAPI
- Pydantic
- Provider abstraction
- Render

### Product frontend

- Next.js
- TypeScript
- Tailwind CSS
- Framer Motion
- lucide-react
- Vercel

---

## Team and Current Ownership

The table below separates core hackathon ownership from responsibilities assigned for continued project development.

| Member | Current ownership |
|---|---|
| **Rama Chandra** | Founder and Product/Architecture Lead. Owns product direction, routing architecture, benchmark strategy, backend decisions, Docker scoring flow, final technical approval, partnerships, and future pilot direction. |
| **Nabothan** | Frontend and UI Contributor. Owns Command Nexus interface work, route visualization, dashboard usability, frontend integration quality, and presentation polish. |
| **Rameen** | QA, Product, and Documentation Contributor. Owns functional QA, scenario testing, demo-flow review, submission-story support, documentation review, and backend simulation validation. |
| **Priyanka Pandey** | Project Operations and Documentation Support. Owns README maintenance, benchmark evidence records, release notes, public-link verification, project archive upkeep, issue-status summaries, and post-hackathon documentation coordination. |

### Responsibilities moved from the founder to Priyanka Pandey

To reduce founder overload and make project maintenance more consistent, the following work is assigned to Priyanka going forward:

| Responsibility | Priyanka's ownership | Rama's involvement |
|---|---|---|
| Root README and documentation index | Maintain current information and formatting | Final approval for technical claims |
| Benchmark and leaderboard evidence | Record dated screenshots, scores, image labels, and result notes | Confirm which result is safe to publish |
| Release notes and changelog | Summarize meaningful releases and experiments | Approve release status |
| Public-link checks | Verify demo, API docs, backend status, and repository links | Handle technical fixes |
| Project archive | Organize final screenshots, pitch files, demo notes, and submission evidence | Provide missing founder/technical material |
| Weekly project status | Collect updates from the team and prepare a short status summary | Set priorities and decisions |
| Issue and PR summary | Maintain a clear open/closed/in-review list | Review and merge technical changes |

Priyanka's assignment is for current and future project operations. It does not retroactively attribute core routing-agent or frontend code that was completed before she joined the workstream.

See [docs/TEAM_OWNERSHIP.md](docs/TEAM_OWNERSHIP.md) for the detailed operating model.

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --hostname 0.0.0.0
```

Never commit real credentials. Store only placeholders in `.env.example`.

---

## Deployment

### Render backend

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Typical environment configuration:

```text
ENVIRONMENT=production
ENABLE_MOCK_CLOUD=true
ENABLE_FIREWORKS=false
ENABLE_OLLAMA=false
CORS_ORIGINS=["http://localhost:3000","https://omniedge-routeiq.vercel.app"]
```

### Vercel frontend

```text
Root Directory: frontend
Build Command: npm run build
Install Command: npm install
```

```text
NEXT_PUBLIC_API_BASE_URL=https://omniedge-routeiq-backend.onrender.com
```

---

## Repository Structure

```text
omniedge-routeiq/
├── backend/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   ├── render.yaml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── track1-*/
│   ├── agent.py
│   ├── local/
│   ├── tests/
│   └── Dockerfile*
├── docs/
│   ├── README.md
│   ├── TEAM_OWNERSHIP.md
│   ├── HACKATHON_RESULT.md
│   ├── architecture.md
│   ├── demo-script.md
│   ├── judging-alignment.md
│   ├── testing-checklist.md
│   └── assets/
├── scripts/
└── README.md
```

---

## Post-Hackathon Priorities

1. Preserve the final scored image, result evidence, and submission history.
2. Reproduce the 19-task benchmark under a documented local test harness.
3. Improve local factual-answer reliability without overfitting to one test set.
4. Add regression gates for accuracy, schema validity, runtime, and missing tasks.
5. Unify the scoring agent and product dashboard through a shared routing-policy layer.
6. Prepare small pilot demonstrations for privacy-sensitive and cost-sensitive workflows.
7. Maintain honest documentation separating evaluated results, internal experiments, and future claims.

---

## Documentation

Start with the [documentation index](docs/README.md).

Key records:

- [Hackathon result](docs/HACKATHON_RESULT.md)
- [Team ownership](docs/TEAM_OWNERSHIP.md)
- [Architecture](docs/architecture.md)
- [Demo script](docs/demo-script.md)
- [Judging alignment](docs/judging-alignment.md)
- [Testing checklist](docs/testing-checklist.md)

---

## Project Status

OmniEdge RouteIQ is a **working hackathon prototype and continuing R&D project**. The repository includes a live product demonstration, a backend routing API, benchmark-agent experiments, test tooling, and evaluation evidence.

It is not yet presented as a production-certified enterprise platform. Security review, broader benchmarking, cost validation, model governance, and pilot testing remain part of the next stage.

---

Built by the OmniEdge RouteIQ team for the AMD Developer Hackathon: ACT II.
MARKDOWN

cat > docs/README.md <<'MARKDOWN'
# OmniEdge RouteIQ Documentation

This directory contains the working documentation for the product dashboard, Track 1 scoring agent, evaluation history, team ownership, QA, and post-hackathon continuation.

## Start Here

| Document | Purpose | Primary maintainer |
|---|---|---|
| [../README.md](../README.md) | Public project overview and current result | Priyanka Pandey, with Rama Chandra approval |
| [HACKATHON_RESULT.md](HACKATHON_RESULT.md) | Dated evaluation and leaderboard record | Priyanka Pandey |
| [TEAM_OWNERSHIP.md](TEAM_OWNERSHIP.md) | Current ownership and handoff model | Priyanka Pandey |
| [architecture.md](architecture.md) | Product and routing architecture | Rama Chandra |
| [demo-script.md](demo-script.md) | Product demo flow | Rameen |
| [judging-alignment.md](judging-alignment.md) | Track and judging alignment | Rama Chandra and Rameen |
| [testing-checklist.md](testing-checklist.md) | QA and release checks | Rameen |

## Documentation Rules

- Separate official evaluator results from internal experiments.
- Date every benchmark or leaderboard record.
- Do not publish private image references, API keys, tokens, or hidden benchmark material.
- Do not claim that an internal local benchmark is an official organizer score.
- Preserve old scored images and result evidence before changing the submission.
- Use the names **Rama Chandra**, **Nabothan**, **Rameen**, and **Priyanka Pandey** consistently.
- Priyanka may update documentation and status records; technical benchmark claims require Rama's approval.
- Rameen reviews QA wording and reproduction steps.
- Nabothan reviews frontend screenshots and UI descriptions when they change.

## Current Documentation Owner

**Priyanka Pandey — Project Operations and Documentation Support**

Current responsibilities:

- README maintenance;
- benchmark evidence records;
- release notes;
- public-link verification;
- project archive organization;
- issue and PR status summaries;
- post-hackathon documentation coordination.

Technical approval remains with **Rama Chandra**.
MARKDOWN

cat > docs/TEAM_OWNERSHIP.md <<'MARKDOWN'
# Team Ownership and Handoff

Updated after the AMD Developer Hackathon: ACT II closing-stage result.

## Operating Principle

Technical ownership, contribution history, and ongoing maintenance are recorded separately. New assignments do not rewrite who completed earlier work.

## Current Team Structure

### Rama Chandra — Founder and Product/Architecture Lead

Owns:

- product direction;
- routing architecture;
- benchmark strategy;
- deterministic and model-routing decisions;
- backend and Docker scoring decisions;
- final technical review;
- release approval;
- partnerships, pilot direction, and external representation.

Rama remains the final approver for benchmark claims, architecture changes, and public technical statements.

### Nabothan — Frontend and UI Contributor

Owns:

- Command Nexus frontend;
- route visualization;
- dashboard layout and usability;
- frontend API integration quality;
- responsive and presentation-ready UI;
- frontend screenshots and demo presentation polish.

### Rameen — QA, Product, and Documentation Contributor

Owns:

- functional QA;
- route and simulation testing;
- demo-flow review;
- submission-story support;
- testing documentation;
- backend simulation validation;
- review of reproduction steps and public QA claims.

### Priyanka Pandey — Project Operations and Documentation Support

Owns:

- root README upkeep;
- documentation index;
- dated benchmark and leaderboard evidence;
- release notes and changelog summaries;
- verification of public links;
- project archive organization;
- weekly project-status summaries;
- issue and pull-request status summaries;
- coordination of post-hackathon documentation.

Priyanka joined the support workstream near the closing stage. Her current role is operational and documentation-focused; it does not retroactively attribute core scoring-agent or frontend implementation.

## Founder Work Reassigned to Priyanka

| Previously handled mainly by Rama | New owner | Approval |
|---|---|---|
| Root README maintenance | Priyanka | Rama approves technical claims |
| Benchmark screenshot and result log | Priyanka | Rama confirms publishable result |
| Release-note drafting | Priyanka | Rama approves release status |
| Demo/API/public-link checks | Priyanka | Technical fixes go to Rama or Nabothan |
| Submission and pitch-file archive | Priyanka | Team supplies source files |
| Weekly status summary | Priyanka | Rama sets priorities |
| Open issue and PR summary | Priyanka | Rama reviews technical closure |

## Handoff Workflow

1. Priyanka collects the latest score, image label, branch, commit, screenshots, and notes.
2. She marks each item as one of:
   - official evaluator result;
   - internal benchmark;
   - experimental candidate;
   - product demo result.
3. Rameen checks the reproduction and QA wording.
4. Nabothan checks frontend links and screenshots when relevant.
5. Rama approves technical claims.
6. Priyanka updates the README, result log, release notes, and archive.
7. The team commits documentation separately from agent-code changes whenever possible.

## Protected Boundaries

Priyanka should not independently:

- change routing thresholds;
- modify scoring-agent logic;
- replace Docker entrypoints;
- publish hidden or private image references;
- claim an internal score as an official score;
- resubmit the hackathon image;
- merge architecture changes without Rama's approval.

These boundaries keep documentation ownership meaningful without creating release risk.
MARKDOWN

cat > docs/HACKATHON_RESULT.md <<'MARKDOWN'
# AMD ACT II Hackathon Result Record

## Final Observed Qualified Result

| Field | Recorded value |
|---|---|
| Project | OmniEdge RouteIQ — Local-First Intelligent Router |
| Team | OmniEdge RouteIQ |
| Track | Hybrid Token-Efficient Routing Agent |
| Final observed leaderboard position | 17th |
| Accuracy | 94.7% |
| Fireworks tokens | 3,100 |
| First submission | July 10, 2026 at 16:59 GMT+5:30 |
| Final recorded resubmission | July 12, 2026 at 20:47 GMT+5:30 |
| Final recorded score time | July 12, 2026 at 21:37 GMT+5:30 |
| Result status | Qualified and scored |

This file records the result observed by the team near the close of the hackathon. Organizer-side reviews, prize decisions, or later corrections should be appended as a new dated section rather than overwriting this record.

## Score Progression

| Recorded stage | Accuracy | Tokens | Notes |
|---|---:|---:|---|
| First scored qualified version | 84.2% | 12,531 | Established valid evaluator execution |
| Improved qualified version | 94.7% | 3,974 | Large accuracy and token improvement |
| Local-first lower-token attempt | 89.5% | 3,421 | Accuracy regression |
| Final protected version | 94.7% | 3,100 | Final observed 17th position |

## Improvement

From 12,531 to 3,100 Fireworks tokens:

```text
Token reduction = 9,431
Percentage reduction = 75.3%
```

The final score also improved from 84.2% to 94.7%.

## Infrastructure Events

Several submission checks displayed organizer-side `INFRA_ERROR` states during the hackathon. The team continued development while preserving known working images and resaving submissions when appropriate.

Documentation rule:

- Record an infrastructure error as an evaluator event.
- Do not automatically classify it as an application defect.
- Check whether the same image previously scored.
- Reproduce locally where possible.
- Preserve the last known qualified result before changing the image.

## Experimental v1.8.1 Note

A v1.8.1 single-pass local-only candidate completed an internal 19-task benchmark with:

- 19 results written;
- 18 of 19 locally correct in the test harness;
- zero Fireworks calls in that internal run;
- one remaining incorrect factual answer.

It was treated as an experiment rather than the protected final submission because official ranking depended first on correctness. The experiment should be used as a future R&D baseline, not presented as the final organizer score.

Private candidate references, hidden benchmark files, and non-public image identifiers must not be copied into public documentation.

## Closing Decision

With only a few hours remaining, the team preserved the 94.7% / 3,100-token qualified submission rather than risk:

- lower accuracy;
- output-schema regression;
- missing tasks;
- runtime failure;
- timeout;
- a new infrastructure error;
- loss of the existing leaderboard position.

## Record Ownership

Primary record maintainer: **Priyanka Pandey**

Approval of technical and benchmark claims: **Rama Chandra**

QA/reproduction review: **Rameen**
MARKDOWN

python3 - <<'PY'
from pathlib import Path
import re

start = "<!-- ROUTEIQ-LATEST-RESULT:START -->"
end = "<!-- ROUTEIQ-LATEST-RESULT:END -->"

block = """<!-- ROUTEIQ-LATEST-RESULT:START -->
## Latest Recorded AMD ACT II Result

| Metric | Result |
|---|---:|
| Final observed position | **17th** |
| Accuracy | **94.7%** |
| Fireworks tokens | **3,100** |
| Initial qualified baseline | 12,531 tokens |
| Token reduction | **75.3%** |

This is the final qualified leaderboard result observed by the team near the hackathon close. A separate v1.8.1 local-only candidate reached 18 of 19 in an internal zero-Fireworks benchmark, but it was retained as an experiment rather than presented as the official final score.

See [`../docs/HACKATHON_RESULT.md`](../docs/HACKATHON_RESULT.md) for the dated result record.
<!-- ROUTEIQ-LATEST-RESULT:END -->"""

paths = sorted({
    *Path(".").glob("track1-*/README.md"),
    *Path(".").glob("track1*/README.md"),
})

for path in paths:
    if path == Path("README.md"):
        continue

    text = path.read_text(encoding="utf-8")

    if start in text and end in text:
        pattern = re.compile(
            re.escape(start) + r".*?" + re.escape(end),
            re.DOTALL,
        )
        updated = pattern.sub(block, text, count=1)
    else:
        lines = text.splitlines()
        insert_at = 0

        for index, line in enumerate(lines):
            if line.startswith("# "):
                insert_at = index + 1
                break

        lines[insert_at:insert_at] = ["", block, ""]
        updated = "\n".join(lines).rstrip() + "\n"

    path.write_text(updated, encoding="utf-8")
    print(f"Updated benchmark block: {path}")
PY

echo
echo "Checking Markdown files..."

python3 - <<'PY'
from pathlib import Path

required = {
    "README.md": [
        "17th",
        "94.7%",
        "3,100",
        "Priyanka Pandey",
        "Nabothan",
        "Rameen",
    ],
    "docs/README.md": [
        "Priyanka Pandey",
        "Documentation Rules",
    ],
    "docs/TEAM_OWNERSHIP.md": [
        "Founder Work Reassigned to Priyanka",
        "Protected Boundaries",
    ],
    "docs/HACKATHON_RESULT.md": [
        "Final Observed Qualified Result",
        "75.3%",
    ],
}

for filename, phrases in required.items():
    path = Path(filename)
    if not path.is_file():
        raise SystemExit(f"Missing expected file: {filename}")

    text = path.read_text(encoding="utf-8")

    for phrase in phrases:
        if phrase not in text:
            raise SystemExit(
                f"{filename} is missing required phrase: {phrase}"
            )

    if "\x00" in text:
        raise SystemExit(f"{filename} contains a null byte")

print("README content checks passed.")
PY

git diff --check

echo
echo "Changed documentation:"
git status --short -- README.md docs \
  'track1-*/README.md' 'track1*/README.md' || true

echo
echo "Diff summary:"
git diff --stat -- README.md docs \
  'track1-*/README.md' 'track1*/README.md' || true

git add README.md \
  docs/README.md \
  docs/TEAM_OWNERSHIP.md \
  docs/HACKATHON_RESULT.md

while IFS= read -r file; do
  git add "$file"
done < <(
  find . -maxdepth 3 -type f -name README.md \
    \( -path './track1-*/*' -o -path './track1*/*' \) \
    -print | sort -u
)

echo
echo "Staged files:"
git diff --cached --name-only

if [[ "$AUTO_COMMIT" == "1" ]]; then
  git commit -m \
    "docs: record final ACT II result and update team ownership"

  if [[ "$AUTO_PUSH" == "1" ]]; then
    git push origin "$(git branch --show-current)"
  fi
else
  echo
  echo "Files are staged but not committed."
  echo "Review with:"
  echo "  git diff --cached"
  echo
  echo "Commit with:"
  echo '  git commit -m "docs: record final ACT II result and update team ownership"'
  echo
  echo "Then push with:"
  echo '  git push origin "$(git branch --show-current)"'
fi

echo
echo "README update completed."
echo "Backup saved at: $BACKUP_DIR"
