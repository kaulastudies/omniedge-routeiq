"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  CheckCircle2,
  Clock3,
  Cloud,
  Cpu,
  Database,
  Gauge,
  GitBranch,
  Lock,
  Play,
  RefreshCcw,
  Route,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type ProviderStatus = {
  name: string;
  available: boolean;
  latency_ms: number | null;
  detail: string;
};

type StatusResponse = {
  service: string;
  version: string;
  environment: string;
  status: string;
  checked_at: string;
  providers: ProviderStatus[];
};

type MetricsResponse = {
  total_requests: number;
  local_requests: number;
  cloud_requests: number;
  hybrid_requests: number;
  fallback_count: number;
  avg_latency_ms: number;
  estimated_cloud_tokens_avoided: number;
  estimated_token_savings_usd: number;
  provider_split_percent: {
    local: number;
    cloud: number;
    hybrid: number;
  };
  recent_decisions: Array<{
    request_id: string;
    target: string;
    provider: string;
    latency_ms: number;
    fallback_used: boolean;
    confidence: number;
    summary: string;
  }>;
};

type RouteResponse = {
  request_id: string;
  created_at: string;
  decision: {
    target: string;
    primary_provider: string;
    backup_providers: string[];
    confidence: number;
    fallback_mode: string;
    reason_codes: string[];
    decision_summary: string;
  };
  classification: {
    privacy_score: number;
    complexity_score: number;
    latency_score: number;
    cost_score: number;
    estimated_input_tokens: number;
    risk_flags: string[];
    explanation: string[];
  };
  provider_response: {
    provider: string;
    model: string;
    text: string;
    latency_ms: number;
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
    total_tokens: number;
  };
  audit_id: string;
  token_savings_estimate_usd: number;
  latency_ms: number;
  fallback_used: boolean;
  audit_timeline: Array<{
    stage: string;
    message: string;
    created_at: string;
  }>;
};

type Simulation = {
  id: string;
  task_type: string;
  privacy_level: string;
  force_route: string | null;
  prompt_preview: string;
};

const samplePrompts = [
  {
    label: "Privacy-first HR review",
    prompt:
      "Summarize this internal employee performance review and identify risks.",
    task_type: "summarization",
    privacy_level: "confidential",
    prefer_local: true,
  },
  {
    label: "Cloud architecture escalation",
    prompt:
      "Design a production-grade multi-region AI deployment architecture with cost and latency tradeoffs.",
    task_type: "architecture",
    privacy_level: "public",
    prefer_local: false,
  },
  {
    label: "Regulated local-first claim",
    prompt:
      "Analyze this patient insurance claim and summarize denial risk without exposing private identifiers.",
    task_type: "analysis",
    privacy_level: "regulated",
    prefer_local: true,
  },
];

function formatUsd(value: number) {
  return `$${value.toFixed(6)}`;
}

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-3xl border border-white/10 bg-white/[0.035] shadow-2xl shadow-black/30 backdrop-blur-xl ${className}`}
    >
      {children}
    </div>
  );
}

function Pill({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "green" | "yellow" | "red" | "blue" | "neutral";
}) {
  const tones = {
    green: "border-emerald-400/30 bg-emerald-400/10 text-emerald-200",
    yellow: "border-amber-400/30 bg-amber-400/10 text-amber-200",
    red: "border-red-400/30 bg-red-400/10 text-red-200",
    blue: "border-sky-400/30 bg-sky-400/10 text-sky-200",
    neutral: "border-white/10 bg-white/5 text-zinc-300",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

export default function Home() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [routeResult, setRouteResult] = useState<RouteResponse | null>(null);
  const [simulations, setSimulations] = useState<Simulation[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState(samplePrompts[0]);
  const [prompt, setPrompt] = useState(samplePrompts[0].prompt);
  const [privacyLevel, setPrivacyLevel] = useState(samplePrompts[0].privacy_level);
  const [taskType, setTaskType] = useState(samplePrompts[0].task_type);
  const [preferLocal, setPreferLocal] = useState(true);
  const [loading, setLoading] = useState(false);

  async function refreshData() {
    try {
      const [statusRes, metricsRes, simRes] = await Promise.all([
        fetch(`${API_BASE}/status`),
        fetch(`${API_BASE}/metrics`),
        fetch(`${API_BASE}/simulations`),
      ]);

      if (statusRes.ok) setStatus(await statusRes.json());
      if (metricsRes.ok) setMetrics(await metricsRes.json());
      if (simRes.ok) {
        const data = await simRes.json();
        setSimulations(data.scenarios || []);
      }
    } catch {
      // UI remains usable even if backend is momentarily unavailable.
    }
  }

  async function runRoute() {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/route`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
          task_type: taskType,
          privacy_level: privacyLevel,
          max_latency_ms: 2000,
          prefer_local: preferLocal,
        }),
      });

      const data = await res.json();
      setRouteResult(data);
      await refreshData();
    } finally {
      setLoading(false);
    }
  }

  async function runSimulation(id: string) {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/simulations/${id}`, {
        method: "POST",
      });
      const data = await res.json();
      setRouteResult(data);
      await refreshData();
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshData();
  }, []);

  const activeDecision = routeResult?.decision?.target || "waiting";
  const provider = routeResult?.provider_response?.provider || "not routed";
  const confidence = routeResult?.decision?.confidence || 0;

  const providerHealth = useMemo(() => {
    if (!status?.providers) return [];
    return status.providers;
  }, [status]);

  return (
    <main className="min-h-screen overflow-hidden bg-[#05070d] text-white">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute left-1/2 top-0 h-[520px] w-[820px] -translate-x-1/2 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="absolute bottom-0 right-0 h-[520px] w-[620px] rounded-full bg-violet-500/10 blur-3xl" />
      </div>

      <section className="relative mx-auto flex max-w-7xl flex-col gap-8 px-6 py-8">
        <header className="flex flex-col gap-6 rounded-[2rem] border border-white/10 bg-white/[0.03] p-6 shadow-2xl shadow-black/40 backdrop-blur-2xl md:flex-row md:items-center md:justify-between">
          <div>
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <Pill tone="blue">
                <Sparkles className="mr-2 h-3.5 w-3.5" />
                AMD ACT II Hackathon
              </Pill>
              <Pill tone={status?.status === "ok" ? "green" : "yellow"}>
                <Activity className="mr-2 h-3.5 w-3.5" />
                API {status?.status || "checking"}
              </Pill>
            </div>

            <h1 className="text-4xl font-semibold tracking-tight md:text-6xl">
              OmniEdge <span className="text-cyan-300">RouteIQ</span>
            </h1>
            <p className="mt-4 max-w-3xl text-sm leading-6 text-zinc-400 md:text-base">
              Enterprise AI routing control plane for local-first privacy,
              cloud escalation, fallback reliability, token savings, and
              explainable audit trails.
            </p>
          </div>

          <button
            onClick={refreshData}
            className="inline-flex items-center justify-center rounded-2xl border border-white/10 bg-white/10 px-5 py-3 text-sm font-medium text-white transition hover:bg-white/15"
          >
            <RefreshCcw className="mr-2 h-4 w-4" />
            Refresh Nexus
          </button>
        </header>

        <div className="grid gap-5 md:grid-cols-4">
          <Card className="p-5">
            <div className="flex items-center justify-between text-zinc-400">
              <span className="text-sm">Total Routes</span>
              <Route className="h-5 w-5 text-cyan-300" />
            </div>
            <div className="mt-4 text-4xl font-semibold">
              {metrics?.total_requests ?? 0}
            </div>
            <p className="mt-2 text-xs text-zinc-500">Live decisions processed</p>
          </Card>

          <Card className="p-5">
            <div className="flex items-center justify-between text-zinc-400">
              <span className="text-sm">Token Savings</span>
              <Zap className="h-5 w-5 text-emerald-300" />
            </div>
            <div className="mt-4 text-4xl font-semibold">
              {formatUsd(metrics?.estimated_token_savings_usd ?? 0)}
            </div>
            <p className="mt-2 text-xs text-zinc-500">
              Estimated cloud spend avoided
            </p>
          </Card>

          <Card className="p-5">
            <div className="flex items-center justify-between text-zinc-400">
              <span className="text-sm">Avg Latency</span>
              <Clock3 className="h-5 w-5 text-violet-300" />
            </div>
            <div className="mt-4 text-4xl font-semibold">
              {Math.round(metrics?.avg_latency_ms ?? 0)}ms
            </div>
            <p className="mt-2 text-xs text-zinc-500">Provider-normalized</p>
          </Card>

          <Card className="p-5">
            <div className="flex items-center justify-between text-zinc-400">
              <span className="text-sm">Fallbacks</span>
              <AlertTriangle className="h-5 w-5 text-amber-300" />
            </div>
            <div className="mt-4 text-4xl font-semibold">
              {metrics?.fallback_count ?? 0}
            </div>
            <p className="mt-2 text-xs text-zinc-500">Reliability events</p>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Card className="p-6">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">Simulation Console</h2>
                <p className="mt-1 text-sm text-zinc-500">
                  Send tasks through RouteIQ and inspect routing decisions.
                </p>
              </div>
              <Bot className="h-6 w-6 text-cyan-300" />
            </div>

            <div className="mb-4 grid gap-3 md:grid-cols-3">
              {samplePrompts.map((item) => (
                <button
                  key={item.label}
                  onClick={() => {
                    setSelectedPrompt(item);
                    setPrompt(item.prompt);
                    setPrivacyLevel(item.privacy_level);
                    setTaskType(item.task_type);
                    setPreferLocal(item.prefer_local);
                  }}
                  className={`rounded-2xl border p-4 text-left text-sm transition ${
                    selectedPrompt.label === item.label
                      ? "border-cyan-400/40 bg-cyan-400/10 text-cyan-100"
                      : "border-white/10 bg-white/[0.03] text-zinc-400 hover:bg-white/[0.06]"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="min-h-36 w-full resize-none rounded-2xl border border-white/10 bg-black/30 p-4 text-sm text-zinc-200 outline-none ring-0 placeholder:text-zinc-600 focus:border-cyan-400/40"
            />

            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <select
                value={privacyLevel}
                onChange={(e) => setPrivacyLevel(e.target.value)}
                className="rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-zinc-200 outline-none"
              >
                <option value="public">Public</option>
                <option value="internal">Internal</option>
                <option value="confidential">Confidential</option>
                <option value="regulated">Regulated</option>
              </select>

              <input
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
                className="rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-zinc-200 outline-none"
                placeholder="task_type"
              />

              <button
                onClick={() => setPreferLocal(!preferLocal)}
                className="rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-zinc-200 transition hover:bg-white/10"
              >
                Prefer Local: {preferLocal ? "Yes" : "No"}
              </button>
            </div>

            <button
              onClick={runRoute}
              disabled={loading}
              className="mt-5 inline-flex w-full items-center justify-center rounded-2xl bg-cyan-300 px-5 py-4 text-sm font-semibold text-black transition hover:bg-cyan-200 disabled:opacity-60"
            >
              {loading ? (
                "Routing..."
              ) : (
                <>
                  Run Route Decision <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </button>

            <div className="mt-6">
              <h3 className="mb-3 text-sm font-medium text-zinc-300">
                Built-in Judge Scenarios
              </h3>
              <div className="grid gap-3 md:grid-cols-2">
                {simulations.map((scenario) => (
                  <button
                    key={scenario.id}
                    onClick={() => runSimulation(scenario.id)}
                    className="group rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left transition hover:border-cyan-400/30 hover:bg-cyan-400/10"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-zinc-200">
                        {scenario.id}
                      </span>
                      <Play className="h-4 w-4 text-zinc-500 group-hover:text-cyan-300" />
                    </div>
                    <p className="mt-2 line-clamp-2 text-xs text-zinc-500">
                      {scenario.prompt_preview}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">Route Decision</h2>
                <p className="mt-1 text-sm text-zinc-500">
                  Explainable routing outcome.
                </p>
              </div>
              <Gauge className="h-6 w-6 text-violet-300" />
            </div>

            <div className="rounded-3xl border border-white/10 bg-black/30 p-5">
              <div className="mb-5 flex items-center justify-between">
                <span className="text-sm text-zinc-500">Selected path</span>
                <Pill
                  tone={
                    activeDecision === "local"
                      ? "green"
                      : activeDecision === "cloud"
                      ? "blue"
                      : activeDecision === "hybrid"
                      ? "yellow"
                      : "neutral"
                  }
                >
                  {activeDecision.toUpperCase()}
                </Pill>
              </div>

              <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div className="flex items-center gap-3">
                  <Cpu className="h-5 w-5 text-emerald-300" />
                  <span className="text-sm">Local</span>
                </div>
                <GitBranch className="h-4 w-4 text-zinc-600" />
                <div className="flex items-center gap-3">
                  <Cloud className="h-5 w-5 text-sky-300" />
                  <span className="text-sm">Cloud</span>
                </div>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-xs text-zinc-500">Provider</p>
                  <p className="mt-2 text-lg font-semibold">{provider}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-xs text-zinc-500">Confidence</p>
                  <p className="mt-2 text-lg font-semibold">
                    {percent(confidence)}
                  </p>
                </div>
              </div>

              <p className="mt-5 text-sm leading-6 text-zinc-400">
                {routeResult?.decision?.decision_summary ||
                  "Run a task to generate an explainable routing decision."}
              </p>
            </div>

            <div className="mt-5 grid gap-3">
              <ScoreRow
                label="Privacy"
                value={routeResult?.classification?.privacy_score ?? 0}
                icon={<Lock className="h-4 w-4" />}
              />
              <ScoreRow
                label="Complexity"
                value={routeResult?.classification?.complexity_score ?? 0}
                icon={<Database className="h-4 w-4" />}
              />
              <ScoreRow
                label="Latency"
                value={routeResult?.classification?.latency_score ?? 0}
                icon={<Clock3 className="h-4 w-4" />}
              />
              <ScoreRow
                label="Cost"
                value={routeResult?.classification?.cost_score ?? 0}
                icon={<Zap className="h-4 w-4" />}
              />
            </div>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="p-6 lg:col-span-1">
            <h2 className="mb-4 text-xl font-semibold">Provider Health</h2>
            <div className="space-y-3">
              {providerHealth.map((item) => (
                <div
                  key={item.name}
                  className="rounded-2xl border border-white/10 bg-black/30 p-4"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{item.name}</span>
                    {item.available ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-300" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-amber-300" />
                    )}
                  </div>
                  <p className="mt-2 text-xs leading-5 text-zinc-500">
                    {item.detail}
                  </p>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6 lg:col-span-1">
            <h2 className="mb-4 text-xl font-semibold">Provider Split</h2>
            <div className="space-y-4">
              <SplitBar
                label="Local"
                value={metrics?.provider_split_percent?.local ?? 0}
              />
              <SplitBar
                label="Cloud"
                value={metrics?.provider_split_percent?.cloud ?? 0}
              />
              <SplitBar
                label="Hybrid"
                value={metrics?.provider_split_percent?.hybrid ?? 0}
              />
            </div>
          </Card>

          <Card className="p-6 lg:col-span-1">
            <h2 className="mb-4 text-xl font-semibold">Fallback Status</h2>
            <div className="rounded-3xl border border-amber-400/20 bg-amber-400/10 p-5">
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-6 w-6 text-amber-200" />
                <div>
                  <p className="font-semibold text-amber-100">
                    Reliability Guard Active
                  </p>
                  <p className="mt-1 text-xs text-amber-100/70">
                    RouteIQ continues execution when Ollama or Fireworks is
                    unavailable.
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-4 rounded-3xl border border-white/10 bg-black/30 p-5">
              <p className="text-xs text-zinc-500">Latest token economics</p>
              <p className="mt-2 text-2xl font-semibold">
                {routeResult
                  ? formatUsd(routeResult.token_savings_estimate_usd)
                  : formatUsd(metrics?.estimated_token_savings_usd ?? 0)}
              </p>
              <p className="mt-2 text-xs text-zinc-500">
                Savings are calculated per routing decision.
              </p>
            </div>
          </Card>
        </div>

        <Card className="p-6">
          <h2 className="mb-4 text-xl font-semibold">Audit Timeline</h2>
          <div className="space-y-3">
            {(routeResult?.audit_timeline || []).length === 0 ? (
              <p className="text-sm text-zinc-500">
                Run a route decision to see the audit trail.
              </p>
            ) : (
              routeResult?.audit_timeline.map((event, index) => (
                <div
                  key={`${event.stage}-${index}`}
                  className="flex gap-4 rounded-2xl border border-white/10 bg-black/30 p-4"
                >
                  <div className="mt-1 h-3 w-3 rounded-full bg-cyan-300 shadow-lg shadow-cyan-300/30" />
                  <div>
                    <p className="text-sm font-medium text-zinc-200">
                      {event.stage}
                    </p>
                    <p className="mt-1 text-sm text-zinc-500">
                      {event.message}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </section>
    </main>
  );
}

function ScoreRow({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs text-zinc-500">
        <span className="flex items-center gap-2">
          {icon}
          {label}
        </span>
        <span>{percent(value)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-cyan-300"
          style={{ width: `${Math.min(100, Math.round(value * 100))}%` }}
        />
      </div>
    </div>
  );
}

function SplitBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-zinc-300">{label}</span>
        <span className="text-zinc-500">{Math.round(value)}%</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-violet-300"
          style={{ width: `${Math.min(100, Math.round(value))}%` }}
        />
      </div>
    </div>
  );
}
