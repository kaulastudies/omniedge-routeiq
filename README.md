<p align="center">
  <img src="./docs/assets/routeiq-mark.svg" width="96" alt="OmniEdge RouteIQ mark" />
</p>

<h1 align="center">OmniEdge RouteIQ</h1>

<p align="center">
  <strong>Hybrid AI routing control plane for local inference, cloud escalation, fallback reliability, token savings, and explainable audit trails.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AMD%20ACT%20II-Hackathon-ED1C24?style=for-the-badge" alt="AMD ACT II Hackathon" />
  <img src="https://img.shields.io/badge/Track-Token%20Efficient%20AI%20Routing-67E8F9?style=for-the-badge" alt="Token Efficient AI Routing" />
  <img src="https://img.shields.io/badge/Frontend-Vercel-black?style=for-the-badge&logo=vercel" alt="Vercel Frontend" />
  <img src="https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge" alt="Render Backend" />
</p>

<p align="center">
  <a href="https://omniedge-routeiq.vercel.app"><strong>Live Demo</strong></a>
  ·
  <a href="https://omniedge-routeiq-backend.onrender.com/docs"><strong>API Docs</strong></a>
  ·
  <a href="https://omniedge-routeiq-backend.onrender.com/status"><strong>Backend Status</strong></a>
</p>

---

## Track 1 Benchmark Result

Best completed evaluator result observed for the protected v1.2 image:

| Metric | Result |
|---|---:|
| Accuracy | **94.7%** |
| Fireworks tokens | **3,974** |
| Previous qualified baseline | 12,531 tokens |
| Token reduction | **68.3%** |

Evaluated image:

```text
ghcr.io/kaulastudies/omniedge-routeiq-track1:v1.2-local-core
```

Execution path:

```text
Deterministic solvers
→ Qwen3 1.7B local inference
→ Fireworks fallback
→ /output/results.json
```

The portal later displayed an infrastructure error during a recheck. These figures record the completed evaluation observed before that recheck.

## Overview

**OmniEdge RouteIQ** is an enterprise-grade AI routing layer built for the AMD ACT II Hackathon.

It routes AI tasks across local inference, cloud inference, hybrid execution, and fallback execution based on:

- privacy sensitivity
- task complexity
- latency requirements
- estimated token cost
- provider availability
- fallback reliability

The goal is simple:

> Do not send every prompt to the cloud by default. Route intelligently.

---

## Problem

Most AI applications send every request directly to a cloud model. That creates major enterprise issues:

| Problem | Impact |
|---|---|
| Sensitive prompts leave the enterprise boundary | Privacy and compliance risk |
| Simple tasks consume cloud tokens unnecessarily | Higher inference cost |
| Provider failures break the experience | Lower reliability |
| Routing decisions are invisible | No auditability or governance |

---

## Solution

OmniEdge RouteIQ acts as a routing control plane between applications and inference providers.

For every request, it classifies the task, selects the best execution path, records provider attempts, handles fallback, and returns an explainable audit trail.

Possible routes:

| Route | Purpose |
|---|---|
| Local | Sensitive or simple tasks suitable for local inference |
| Cloud | Public or complex tasks needing stronger remote inference |
| Hybrid | Confidential tasks needing local privacy handling plus cloud-capable reasoning |
| Fallback | Recovery path when Ollama, Fireworks, or another provider is unavailable |

---

## Live Links

| Layer | URL |
|---|---|
| Frontend Demo | https://omniedge-routeiq.vercel.app |
| Backend API Docs | https://omniedge-routeiq-backend.onrender.com/docs |
| Backend Status | https://omniedge-routeiq-backend.onrender.com/status |
| GitHub Repository | https://github.com/kaulastudies/omniedge-routeiq |

---

## Core Features

- Local-first routing for sensitive prompts
- Cloud escalation for complex tasks
- Hybrid routing for privacy-aware advanced reasoning
- Provider abstraction for Ollama, Fireworks AI, and mock cloud fallback
- Fallback handling when providers fail
- Token savings estimation
- Latency tracking
- Provider health checks
- Metrics endpoint
- Explainable audit timeline
- Premium Command Nexus dashboard

---

## Command Nexus Dashboard

The frontend is a dark-mode enterprise dashboard inspired by modern SaaS control planes.

It includes:

- route decision panel
- token savings card
- latency card
- local/cloud/hybrid split
- provider health monitor
- fallback status
- simulation console
- audit timeline

---

## Architecture

```txt
User Prompt
   ↓
Next.js Command Nexus Dashboard
   ↓
FastAPI /route endpoint
   ↓
Routing Classifier
   ↓
Decision Engine
   ↓
Provider Registry
   ↓
Ollama Local Provider / Fireworks Cloud Provider / Mock Cloud Fallback
   ↓
Normalized Provider Response
   ↓
Metrics + Audit Timeline
   ↓
Dashboard Visualization
```

---

## Routing Logic

RouteIQ evaluates every request across five dimensions:

| Dimension | Question |
|---|---|
| Privacy | Is the prompt sensitive, confidential, or regulated? |
| Complexity | Does the task require stronger reasoning? |
| Latency | Does the user need a fast response? |
| Cost | Can this avoid unnecessary cloud tokens? |
| Reliability | Are providers available, and what fallback is safest? |

The decision engine then selects local, cloud, hybrid, or fallback execution.

---

## API Endpoints

```txt
GET  /status
GET  /metrics
GET  /simulations
POST /simulations/{scenario_id}
POST /route
GET  /audit/recent
```

Example request:

```bash
curl -X POST https://omniedge-routeiq-backend.onrender.com/route \
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

## Judge Demo Scenarios

| Scenario | What It Demonstrates |
|---|---|
| `local_sensitive_prompt` | Local-first privacy routing |
| `cloud_complex_architecture` | Cloud-capable architecture reasoning |
| `hybrid_confidential_code` | Hybrid routing for confidential code review |
| `fallback_no_key_demo` | Fallback reliability when cloud provider keys are unavailable |

---

## Tech Stack

### Frontend

<p>
  <img src="https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=nextdotjs" alt="Next.js" />
  <img src="https://img.shields.io/badge/Tailwind-CSS-38BDF8?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Framer-Motion-FF69B4?style=flat-square" alt="Framer Motion" />
  <img src="https://img.shields.io/badge/Vercel-Deployed-black?style=flat-square&logo=vercel" alt="Vercel" />
</p>

- Next.js
- Tailwind CSS
- Framer Motion
- lucide-react
- Vercel

### Backend

<p>
  <img src="https://img.shields.io/badge/Python-FastAPI-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Pydantic-Validation-E92063?style=flat-square" alt="Pydantic" />
  <img src="https://img.shields.io/badge/Render-Deployed-46E3B7?style=flat-square" alt="Render" />
</p>

- Python
- FastAPI
- Pydantic
- Provider abstraction
- Render

### Providers

- Ollama local provider
- Fireworks AI cloud provider
- Mock cloud fallback provider

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

---

## Deployment

### Render Backend

```txt
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```txt
ENVIRONMENT=production
ENABLE_MOCK_CLOUD=true
ENABLE_FIREWORKS=false
ENABLE_OLLAMA=false
CORS_ORIGINS=["http://localhost:3000","https://omniedge-routeiq.vercel.app"]
```

### Vercel Frontend

```txt
Root Directory: frontend
Build Command: npm run build
Install Command: npm install
```

Environment variable:

```txt
NEXT_PUBLIC_API_BASE_URL=https://omniedge-routeiq-backend.onrender.com
```

---

## Team

| Member | Ownership |
|---|---|
| Rama Chandra | Founder/Product Lead, backend architecture, routing logic, API integration, final submission strategy |
| Nabothanan | Frontend, UI/UX, Command Nexus dashboard |
| Rameen | QA, demo video script, submission story, judging alignment, and backend simulation review |

---

## Why This Can Win

OmniEdge RouteIQ is not another chatbot.

It is infrastructure for the next generation of AI applications.

It helps enterprises reduce cloud token waste, protect sensitive prompts, recover from provider failures, and understand every inference decision through a transparent audit trail.

> AI inference should not be one-size-fits-all. It should be routed intelligently.

---

## Repository Structure

```txt
omniedge-routeiq/
├── backend/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   ├── render.yaml
│   └── requirements.txt
├── frontend/
│   ├── src/app/
│   ├── public/
│   └── package.json
├── docs/
│   ├── architecture.md
│   ├── demo-script.md
│   ├── judging-alignment.md
│   ├── testing-checklist.md
│   └── assets/
└── README.md
```

---

## Final Submission Links

| Item | Link |
|---|---|
| Live Product Demo | https://omniedge-routeiq.vercel.app |
| API Documentation | https://omniedge-routeiq-backend.onrender.com/docs |
| Backend Health Check | https://omniedge-routeiq-backend.onrender.com/status |
| Source Code | https://github.com/kaulastudies/omniedge-routeiq |

---

<p align="center">
  <strong>Built for the AMD ACT II Hackathon.</strong>
</p>
