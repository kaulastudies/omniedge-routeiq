## Issue #5: Prepare Final Demo Video Script for OmniEdge RouteIQ
State: CLOSED
Author: kaulastudies
Closed At: 2026-07-05T12:57:28Z
URL: https://github.com/kaulastudies/omniedge-routeiq/issues/5

### Body
## Goal

Prepare the final 2–3 minute demo video script for OmniEdge RouteIQ.

The script must help judges understand the project quickly, clearly, and professionally.

## Product Positioning

OmniEdge RouteIQ is not a chatbot.

It is an enterprise AI routing control plane that decides whether each AI task should run locally, in the cloud, through hybrid execution, or through fallback.

## Demo Links

Live Dashboard:
https://omniedge-routeiq.vercel.app

Backend API Docs:
https://omniedge-routeiq-backend.onrender.com/docs

GitHub Repo:
https://github.com/kaulastudies/omniedge-routeiq

## Required Message

The script must explain:

1. The problem:
   - Most AI apps send every prompt directly to the cloud.
   - This increases token cost.
   - It can expose sensitive data.
   - It gives no audit trail for routing decisions.

2. The solution:
   - RouteIQ scores every prompt using privacy, complexity, latency, cost, and provider availability.
   - It chooses local, cloud, hybrid, or fallback execution.
   - It records an explainable audit trail.

3. The demo:
   - Show live dashboard.
   - Run a local-first scenario.
   - Run a fallback scenario.
   - Run a hybrid/confidential code scenario.
   - Show token savings, provider health, and audit timeline.

## Draft Script To Start From

“Most AI apps send every prompt directly to a cloud model. That creates privacy risk, unnecessary token cost, and poor visibility into inference decisions.

OmniEdge RouteIQ solves this by acting as an AI routing control plane.

For every request, RouteIQ evaluates privacy, complexity, latency, cost, and provider availability. Then it decides whether the task should run locally, in the cloud, through hybrid execution, or through fallback.

Here is the live Command Nexus dashboard.

First, I’ll run a sensitive enterprise scenario. RouteIQ detects confidential data and selects local-first routing. Since the deployed demo environment does not have Ollama running, the system safely falls back to the mock cloud provider instead of failing.

Now I’ll run a cloud fallback scenario. This forces a cloud route. Fireworks is not configured in this demo deployment, so RouteIQ detects the provider failure, switches to fallback, and records the full process in the audit timeline.

Next, I’ll run the hybrid confidential code scenario. This demonstrates how RouteIQ can support privacy-aware routing for internal developer workflows.

The dashboard also shows token savings, average latency, provider split, fallback count, and provider health.

The most important part is the audit timeline. Every decision is explainable: request received, classification completed, decision selected, provider attempted, fallback triggered, provider succeeded, and metrics recorded.

OmniEdge RouteIQ is not another chatbot. It is infrastructure for enterprise AI systems that need privacy, cost control, fallback reliability, and inference governance.”

## Acceptance Criteria

- Script is 2–3 minutes when spoken.
- Script explains the problem clearly.
- Script explains RouteIQ as an AI routing control plane.
- Script mentions local, cloud, hybrid, and fallback routing.
- Script mentions token savings and audit trail.
- No unrelated project names.
- No ClaimSetu, Stellar, SCF, YouTube, Instagram, hospital, or insurance references.

### Comments
- @kaulastudies: Organized during OmniEdge RouteIQ professional issue audit with owner, milestone, and labels.
- @r2meen: Good [morning/afternoon]. Most AI applications send every prompt directly to a cloud model. While that works, it creates three major challenges for enterprises: sensitive data may leave the organization, simple tasks consume unnecessary cloud tokens, and there is little visibility into why a particular AI provider was chosen.  OmniEdge RouteIQ solves this problem by acting as an enterprise AI routing control plane. Instead of treating every request the same, RouteIQ evaluates each prompt across five dimensions: privacy, complexity, latency requirements, estimated cost, and provider availability. Based on that analysis, it intelligently routes the request to local inference, cloud inference, hybrid execution, or a fallback provider.  Let me show you the live Command Nexus dashboard.  For the first scenario, I'll run a sensitive enterprise prompt. RouteIQ identifies the request as confidential and selects a local-first execution path to help keep sensitive data within the enterprise environment. In this deployed demo, Ollama is intentionally not running, so instead of failing, RouteIQ automatically switches to the fallback provider while recording every decision along the way.  Next, I'll run the fallback scenario. This simulates a cloud provider being unavailable. RouteIQ detects the failure, selects the fallback provider, successfully completes the request, and captures the complete routing process in the audit timeline. This demonstrates how applications can remain reliable even when an AI provider is unavailable.  Now I'll demonstrate the hybrid confidential code scenario. This represents workflows where privacy and advanced reasoning both matter. RouteIQ selects a hybrid execution strategy, showing how organizations can balance data protection with the capabilities of more powerful AI models.  As these scenarios run, the dashboard updates in real time. You can see the selected route, estimated token savings, response latency, provider health, routing distribution, fallback activity, and recent metrics.  One of the most important features is the explainable audit timeline. Every routing decision is transparent—from request received, classification completed, routing decision selected, provider attempted, fallback triggered if necessary, provider response received, and metrics recorded. This gives enterprises the visibility and governance that traditional AI integrations often lack.  OmniEdge RouteIQ is not another chatbot. It is intelligent infrastructure for enterprise AI applications, enabling privacy-aware routing, lower inference costs through smarter model selection, resilient fallback handling, and fully explainable AI routing decisions.  Thank you. 

## Issue #6: Create Demo Video Click-Flow and Recording Checklist
State: CLOSED
Author: kaulastudies
Closed At: 2026-07-05T13:05:34Z
URL: https://github.com/kaulastudies/omniedge-routeiq/issues/6

### Body
## Goal

Create the exact click-flow for recording the OmniEdge RouteIQ demo video.

The video should feel like a polished enterprise SaaS demo, not a random screen recording.

## Recording URL

Use the live frontend:

https://omniedge-routeiq.vercel.app

Before recording, open this once to wake the backend:

https://omniedge-routeiq-backend.onrender.com/status

## Exact Recording Flow

### Step 1 — Open Dashboard

Open:

https://omniedge-routeiq.vercel.app

Show the hero section:

- OmniEdge RouteIQ
- Command Nexus dashboard
- Metrics cards
- Simulation Console
- Route Decision
- Provider Health
- Audit Timeline

Narration:

“This is OmniEdge RouteIQ, a hybrid AI routing control plane for privacy, cost savings, fallback reliability, and auditability.”

### Step 2 — Click Refresh Nexus

Click:

Refresh Nexus

Purpose:

- Show backend connection is live.
- Show provider health.
- Show current metrics.

Narration:

“The dashboard is connected to the live FastAPI backend deployed on Render.”

### Step 3 — Run Local Sensitive Scenario

Click:

local_sensitive_prompt

Show:

- Selected path
- Privacy score
- Provider
- Fallback status
- Audit timeline

Narration:

“Here RouteIQ detects sensitive enterprise data and chooses local-first routing. Since Ollama is unavailable in this cloud demo environment, the system safely falls back and records that event.”

### Step 4 — Run Cloud/Fallback Scenario

Click:

fallback_no_key_demo

Show:

- Fireworks attempted
- Fireworks failed due to missing key
- Mock cloud fallback succeeded
- Audit timeline updated

Narration:

“This scenario demonstrates provider reliability. RouteIQ does not fail when a provider is unavailable. It routes through fallback and preserves the full audit trail.”

### Step 5 — Run Hybrid Scenario

Click:

hybrid_confidential_code

Show:

- Route decision
- Privacy/complexity scores
- Audit trail
- Provider attempts

Narration:

“This scenario represents confidential developer workflows where RouteIQ can support privacy-aware hybrid execution.”

### Step 6 — Show Metrics

Show:

- Total Routes
- Token Savings
- Avg Latency
- Fallbacks
- Provider Split

Narration:

“RouteIQ tracks inference cost, routing split, latency, and fallback events so teams can understand how AI infrastructure is being used.”

### Step 7 — Closing

Narration:

“OmniEdge RouteIQ is not a chatbot. It is the missing control plane for enterprise AI inference.”

## Final Recording Checklist

Before recording:

- Backend status page opens successfully.
- Frontend dashboard loads.
- Refresh Nexus works.
- Run Route Decision works.
- Judge scenarios work.
- Audit timeline appears.
- No unrelated scenario text appears.
- Browser zoom is set to 90% or 100%.
- Notifications are off.
- Only needed tabs are open.

## Acceptance Criteria

- Recording flow is clear.
- Every click is listed.
- Narration guidance is included.
- Final checklist is included.
- No unrelated project references.

### Comments
- @kaulastudies: Organized during OmniEdge RouteIQ professional issue audit with owner, milestone, and labels.
- @r2meen:  OmniEdge RouteIQ — Demo Recording Click Flow   Pre-Recording Setup  1. Open the backend status page:     *  https://omniedge-routeiq-backend.onrender.com/status    *  Wait until the page loads successfully to wake the Render backend.  2. Open the frontend:     *  https://omniedge-routeiq.vercel.app/  3. Before recording:     *  Browser zoom: 90% or 100%    *  Turn off notifications.    *  Close unnecessary tabs and applications.    *  Ensure the dashboard is fully loaded.  ---  # Step 1 — Open Dashboard  Action:  Open the homepage and pause for a few seconds.  Show:  *  OmniEdge RouteIQ title *  Command Nexus dashboard *  Metrics cards *  Simulation Console *  Route Decision panel *  Provider Health *  Audit Timeline  Narration:  > "This is OmniEdge RouteIQ, a hybrid AI routing control plane for privacy, cost savings, fallback reliability, and explainable AI routing. Instead of sending every request directly to a cloud model, RouteIQ intelligently decides where each AI task should execute."  ---  # Step 2 — Refresh Nexus  Action:  Click Refresh Nexus  Wait for:  *  Provider Health updates *  Metrics refresh *  Backend connection confirmation  Narration:  > "The dashboard is connected to a live FastAPI backend deployed on Render. Refresh Nexus retrieves the latest provider health and routing metrics."  ---  # Step 3 — Run Local Sensitive Scenario  Action:  In the Simulation Console, click: local_sensitive_prompt. Wait for the route to complete.  Highlight:  *  Route Decision *  Privacy score *  Selected provider *  Fallback status *  Audit Timeline entries  Narration:  > "This scenario contains sensitive enterprise information. RouteIQ selects a local-first execution strategy. Because Ollama is unavailable in this cloud-hosted demo environment, the system automatically switches to the fallback provider instead of failing. Every routing decision is captured in the audit timeline."  ---  # Step 4 — Run Cloud/Fallback Scenario  Action  Click: fallback_no_key_demo and then wait for execution.  Highlight:  *  Fireworks provider attempt *  Provider failure *  Mock cloud fallback *  Updated audit timeline  Narration:  > "This demonstrates provider reliability. RouteIQ first attempts the configured cloud provider. Since the provider is unavailable in this deployment, it automatically routes through the fallback provider, ensuring the request still succeeds while preserving a complete audit trail."  ---  # Step 5 — Run Hybrid Scenario  Action:  Click on hybrid_confidential_code and then allow the simulation to complete.  Highlight:  *  Route Decision *  Privacy score *  Complexity score *  Provider attempts *  Audit Timeline  Narration:  > "This scenario represents confidential developer workflows. RouteIQ identifies both privacy requirements and higher reasoning complexity, demonstrating how hybrid execution can support enterprise AI workflows."  ---  # Step 6 — Show Dashboard Metrics  Action:  Slowly move across the dashboard and highlight:  *  Total Routes *  Estimated Token Savings *  Average Latency *  Fallback Count *  Provider Split *  Provider Health *  Audit Timeline  Narration:  > "Beyond routing requests, RouteIQ provides operational visibility. Teams can monitor estimated token savings, routing distribution, response latency, provider health, fallback activity, and every inference decision through an explainable audit timeline."  ---  # Step 7 — Closing  Action:  Return to the top of the dashboard so the product name and dashboard are visible and pause for a few seconds before ending the recording.  Narration:  > "OmniEdge RouteIQ is not a chatbot. It is the intelligent control plane for enterprise AI inference, enabling privacy-aware routing, cost optimization, resilient fallback handling, and transparent AI governance."  ---  Final Recording Checklist:  Before pressing Record:  *  Backend status page opens successfully. *  Frontend dashboard loads completely. *  Refresh Nexus updates successfully. *  local_sensitive_prompt executes correctly. *  fallback_no_key_demo executes correctly. *  hybrid_confidential_code executes correctly. *  Route Decision panel updates after each scenario. *  Audit Timeline displays routing events. *  Metrics update correctly. *  Browser zoom is set to 90% or 100%. *  Notifications are disabled. *  Only required browser tabs are open. *  Record at 1080p resolution if possible. *  Speak slowly and keep the total presentation between 2 and 3 minutes.

