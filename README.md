<p align="center">
  <img
    src="./docs/assets/routeiq-mark.svg"
    width="104"
    alt="OmniEdge RouteIQ mark"
  />
</p>

<h1 align="center">OmniEdge RouteIQ</h1>

<p align="center">
  <strong>
    Local-first intelligent routing for private, reliable,
    and token-efficient AI execution.
  </strong>
</p>

<p align="center">
  <img
    src="https://img.shields.io/badge/AMD%20Developer%20Hackathon-ACT%20II-ED1C24?style=for-the-badge"
    alt="AMD Developer Hackathon ACT II"
  />
  <img
    src="https://img.shields.io/badge/Track-Hybrid%20Token--Efficient%20Routing-2563EB?style=for-the-badge"
    alt="Hybrid Token-Efficient Routing Agent"
  />
</p>

<p align="center">
  <img
    src="https://img.shields.io/badge/Accuracy-100.0%25-16A34A?style=flat-square"
    alt="100 percent accuracy"
  />
  <img
    src="https://img.shields.io/badge/Qualified%20Tasks-19%20of%2019-16A34A?style=flat-square"
    alt="19 of 19 tasks"
  />
  <img
    src="https://img.shields.io/badge/Fireworks%20Tokens-3%2C242-F59E0B?style=flat-square"
    alt="3,242 Fireworks tokens"
  />
  <img
    src="https://img.shields.io/badge/Observed%20Rank-30th-7C3AED?style=flat-square"
    alt="Observed rank 30"
  />
</p>

<p align="center">
  <img
    src="https://img.shields.io/badge/Frontend-Next.js-black?style=flat-square&logo=next.js"
    alt="Next.js frontend"
  />
  <img
    src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi"
    alt="FastAPI backend"
  />
  <img
    src="https://img.shields.io/badge/Deployment-Vercel-black?style=flat-square&logo=vercel"
    alt="Vercel deployment"
  />
  <img
    src="https://img.shields.io/badge/API-Render-46E3B7?style=flat-square"
    alt="Render backend"
  />
</p>

<p align="center">
  <a href="https://omniedge-routeiq.vercel.app">
    <strong>Live Demo</strong>
  </a>
  &nbsp;•&nbsp;
  <a href="https://omniedge-routeiq-backend.onrender.com/docs">
    <strong>API Documentation</strong>
  </a>
  &nbsp;•&nbsp;
  <a href="https://omniedge-routeiq-backend.onrender.com/status">
    <strong>Backend Status</strong>
  </a>
  &nbsp;•&nbsp;
  <a href="https://github.com/kaulastudies/omniedge-routeiq">
    <strong>Source Code</strong>
  </a>
</p>

---

## AMD ACT II — Final Observed Track 1 Result

<!-- ROUTEIQ-SECTION-TAGS:amd-act-ii-final-observed-track-1-result -->
<p>
  <img src="https://img.shields.io/badge/Result-Qualified-16A34A?style=flat-square" alt="Qualified result" />
  <img src="https://img.shields.io/badge/Accuracy-100.0%25-16A34A?style=flat-square" alt="100 percent accuracy" />
  <img src="https://img.shields.io/badge/Tokens-3%2C242-F59E0B?style=flat-square" alt="3,242 tokens" />
  <img src="https://img.shields.io/badge/Tasks-19%2F19-2563EB?style=flat-square" alt="19 of 19 tasks" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

The final qualified leaderboard snapshot observed near the close of the AMD Developer Hackathon: ACT II was:

| Metric | Final observed result |
|---|---:|
| Track | Hybrid Token-Efficient Routing Agent |
| Leaderboard position | **30th** |
| Accuracy | **100.0%** |
| Fireworks tokens | **3,242** |
| Qualified tasks | **19 of 19** |
| Initial qualified baseline | 12,531 tokens at 84.2% accuracy |
| Token reduction from initial baseline | **74.1%** |
| Status | Qualified, scored, and preserved |

After reaching 100% accuracy, the team stopped further high-risk token experiments and preserved the scored candidate to avoid regressions, schema errors, timeouts, or infrastructure failures.

> This is the final leaderboard result observed by the team. Prize decisions, manual reviews, or organizer-side adjustments may be reported separately.

### Benchmark progression

| Stage | Accuracy | Fireworks tokens | Outcome |
|---|---:|---:|---|
| Early qualified run | 84.2% | 12,531 | Established a valid scoring baseline |
| Major optimization | 94.7% | 3,974 | Reached the top 10 in an earlier snapshot |
| Local-first experiment | 89.5% | 3,421 | Lower token use, but accuracy regressed |
| Final scored run | **100.0%** | **3,242** | Latest verified score, observed at **30th position**, with all 19 tasks correct |

### Final experimental learning

Before the final score, the v1.8.1 single-pass candidate reached 18 of 19 in the internal benchmark. The later official evaluator run achieved 100% accuracy with 3,242 Fireworks tokens, confirming that the final candidate resolved the remaining benchmark case.

The internal zero-Fireworks experiment remains useful research for future token reduction, while the 100% scored candidate is preserved as the final benchmark baseline.

---

## What RouteIQ Does

<!-- ROUTEIQ-SECTION-TAGS:what-routeiq-does -->
<p>
  <img src="https://img.shields.io/badge/Approach-Local--First-0F766E?style=flat-square" alt="Local first" />
  <img src="https://img.shields.io/badge/Execution-Privacy--Aware-7C3AED?style=flat-square" alt="Privacy aware" />
  <img src="https://img.shields.io/badge/Optimization-Token--Efficient-F59E0B?style=flat-square" alt="Token efficient" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

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

<!-- ROUTEIQ-SECTION-TAGS:two-working-layers -->
<p>
  <img src="https://img.shields.io/badge/Layer%201-Track%201%20Agent-2563EB?style=flat-square" alt="Track 1 scoring agent" />
  <img src="https://img.shields.io/badge/Layer%202-Command%20Nexus-7C3AED?style=flat-square" alt="Command Nexus dashboard" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

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

<!-- ROUTEIQ-SECTION-TAGS:core-features -->
<p>
  <img src="https://img.shields.io/badge/Core-Intelligent%20Routing-2563EB?style=flat-square" alt="Intelligent routing" />
  <img src="https://img.shields.io/badge/Safety-Strict%20Validation-16A34A?style=flat-square" alt="Strict validation" />
  <img src="https://img.shields.io/badge/Governance-Audit%20Trail-7C3AED?style=flat-square" alt="Audit trail" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

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

<!-- ROUTEIQ-SECTION-TAGS:product-architecture -->
<p>
  <img src="https://img.shields.io/badge/Frontend-Next.js-black?style=flat-square&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/API-FastAPI-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Agent-Python-3776AB?style=flat-square&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/Runtime-Docker-2496ED?style=flat-square&logo=docker" alt="Docker" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

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

<!-- ROUTEIQ-SECTION-TAGS:live-links -->
<p>
  <img src="https://img.shields.io/badge/Demo-Live-16A34A?style=flat-square" alt="Live demo" />
  <img src="https://img.shields.io/badge/Frontend-Vercel-black?style=flat-square&logo=vercel" alt="Vercel" />
  <img src="https://img.shields.io/badge/Backend-Render-46E3B7?style=flat-square" alt="Render" />
  <img src="https://img.shields.io/badge/Repository-GitHub-181717?style=flat-square&logo=github" alt="GitHub" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

| Layer | Link |
|---|---|
| Frontend demo | https://omniedge-routeiq.vercel.app |
| Backend API documentation | https://omniedge-routeiq-backend.onrender.com/docs |
| Backend health check | https://omniedge-routeiq-backend.onrender.com/status |
| Source repository | https://github.com/kaulastudies/omniedge-routeiq |

---

## API Endpoints

<!-- ROUTEIQ-SECTION-TAGS:api-endpoints -->
<p>
  <img src="https://img.shields.io/badge/API-REST-2563EB?style=flat-square" alt="REST API" />
  <img src="https://img.shields.io/badge/Framework-FastAPI-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Format-JSON-F59E0B?style=flat-square" alt="JSON" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

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

<!-- ROUTEIQ-SECTION-TAGS:demo-scenarios -->
<p>
  <img src="https://img.shields.io/badge/Route-Local-0F766E?style=flat-square" alt="Local route" />
  <img src="https://img.shields.io/badge/Route-Cloud-2563EB?style=flat-square" alt="Cloud route" />
  <img src="https://img.shields.io/badge/Route-Hybrid-7C3AED?style=flat-square" alt="Hybrid route" />
  <img src="https://img.shields.io/badge/Route-Fallback-F59E0B?style=flat-square" alt="Fallback route" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

| Scenario | Demonstrates |
|---|---|
| `local_sensitive_prompt` | Privacy-aware local-first routing |
| `cloud_complex_architecture` | Cloud-capable reasoning |
| `hybrid_confidential_code` | Hybrid handling for confidential code |
| `fallback_no_key_demo` | Recovery when a cloud key or provider is unavailable |

---

## Tech Stack

<!-- ROUTEIQ-SECTION-TAGS:tech-stack -->
<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-Container-2496ED?style=flat-square&logo=docker" alt="Docker" />
  <img src="https://img.shields.io/badge/Fireworks-AI-F59E0B?style=flat-square" alt="Fireworks AI" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

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

<!-- ROUTEIQ-SECTION-TAGS:team-and-current-ownership -->
<p>
  <img src="https://img.shields.io/badge/Team-Core%20Contributors-2563EB?style=flat-square" alt="Core contributors" />
  <img src="https://img.shields.io/badge/Workflow-Clear%20Ownership-16A34A?style=flat-square" alt="Clear ownership" />
  <img src="https://img.shields.io/badge/Quality-QA%20%26%20Verification-7C3AED?style=flat-square" alt="QA and verification" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

The table below separates core hackathon ownership from responsibilities assigned for continued project development.

| Member | Current ownership |
|---|---|
| **Rama Chandra** | Founder and Product/Architecture Lead. Owns product direction, routing architecture, benchmark strategy, backend decisions, Docker scoring flow, final technical approval, partnerships, and future pilot direction. |
| **[Nabothan](https://github.com/Nabothdaniel)** | Frontend and UI Contributor. Owns Command Nexus interface work, route visualization, dashboard usability, frontend integration quality, and presentation polish. |
| **[Rameen](https://github.com/r2meen)** | QA, Product, and Documentation Contributor. Owns functional QA, scenario testing, demo-flow review, submission-story support, documentation review, and backend simulation validation. |
| **[Franklin Josva](https://github.com/franklinjosva2605-dot)** | Final Verification and Documentation Contributor. Supports final leaderboard-result verification, final GHCR image validation, README review, and public-link QA. |
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

<!-- ROUTEIQ-SECTION-TAGS:local-development -->
<p>
  <img src="https://img.shields.io/badge/Backend-Python-3776AB?style=flat-square&logo=python" alt="Python backend" />
  <img src="https://img.shields.io/badge/Frontend-Node.js-339933?style=flat-square&logo=node.js" alt="Node.js frontend" />
  <img src="https://img.shields.io/badge/Quality-Automated%20Tests-16A34A?style=flat-square" alt="Automated tests" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

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

<!-- ROUTEIQ-SECTION-TAGS:deployment -->
<p>
  <img src="https://img.shields.io/badge/Frontend-Vercel-black?style=flat-square&logo=vercel" alt="Vercel" />
  <img src="https://img.shields.io/badge/Backend-Render-46E3B7?style=flat-square" alt="Render" />
  <img src="https://img.shields.io/badge/Containers-GHCR-181717?style=flat-square&logo=github" alt="GitHub Container Registry" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

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

<!-- ROUTEIQ-SECTION-TAGS:repository-structure -->
<p>
  <img src="https://img.shields.io/badge/Structure-Monorepo-2563EB?style=flat-square" alt="Monorepo" />
  <img src="https://img.shields.io/badge/Included-Tests-16A34A?style=flat-square" alt="Tests included" />
  <img src="https://img.shields.io/badge/Included-Documentation-7C3AED?style=flat-square" alt="Documentation included" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

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

<!-- ROUTEIQ-SECTION-TAGS:post-hackathon-priorities -->
<p>
  <img src="https://img.shields.io/badge/Stage-Continuing%20R%26D-7C3AED?style=flat-square" alt="Continuing research" />
  <img src="https://img.shields.io/badge/Priority-Regression%20Safety-16A34A?style=flat-square" alt="Regression safety" />
  <img src="https://img.shields.io/badge/Next-Pilot%20Validation-2563EB?style=flat-square" alt="Pilot validation" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

1. Preserve the final scored image, result evidence, and submission history.
2. Reproduce the 19-task benchmark under a documented local test harness.
3. Improve local factual-answer reliability without overfitting to one test set.
4. Add regression gates for accuracy, schema validity, runtime, and missing tasks.
5. Unify the scoring agent and product dashboard through a shared routing-policy layer.
6. Prepare small pilot demonstrations for privacy-sensitive and cost-sensitive workflows.
7. Maintain honest documentation separating evaluated results, internal experiments, and future claims.

---

## Documentation

<!-- ROUTEIQ-SECTION-TAGS:documentation -->
<p>
  <img src="https://img.shields.io/badge/Docs-Architecture-2563EB?style=flat-square" alt="Architecture documentation" />
  <img src="https://img.shields.io/badge/Docs-Demo%20Guide-7C3AED?style=flat-square" alt="Demo guide" />
  <img src="https://img.shields.io/badge/Docs-Testing-16A34A?style=flat-square" alt="Testing documentation" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

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

<!-- ROUTEIQ-SECTION-TAGS:project-status -->
<p>
  <img src="https://img.shields.io/badge/Status-Working%20Prototype-16A34A?style=flat-square" alt="Working prototype" />
  <img src="https://img.shields.io/badge/Evaluation-100.0%25%20Accuracy-16A34A?style=flat-square" alt="100 percent accuracy" />
  <img src="https://img.shields.io/badge/Stage-Continuing%20R%26D-7C3AED?style=flat-square" alt="Continuing R and D" />
</p>
<!-- /ROUTEIQ-SECTION-TAGS -->

OmniEdge RouteIQ is a **working hackathon prototype and continuing R&D project**. The repository includes a live product demonstration, a backend routing API, benchmark-agent experiments, test tooling, and evaluation evidence.

It is not yet presented as a production-certified enterprise platform. Security review, broader benchmarking, cost validation, model governance, and pilot testing remain part of the next stage.

---

Built by the OmniEdge RouteIQ team for the AMD Developer Hackathon: ACT II.
