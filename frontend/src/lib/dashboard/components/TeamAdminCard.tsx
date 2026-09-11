import { useState, useEffect } from "react";
import { TileCard } from "./TileCard";
import { toast } from "sonner";
import { useRouteIQ } from "@/hooks/use-route-iq";
import { PiPlayCircle } from "react-icons/pi";
import { PiSpinner } from "react-icons/pi";

const SCENARIO_META: Record<string, { title: string; tag: string }> = {
  local_sensitive_prompt: {
    title: "Gemma High Confidence",
    tag: "Local",
  },
  cloud_complex_architecture: {
    title: "Fireworks Fallback",
    tag: "Cloud",
  },
  hybrid_confidential_code: {
    title: "Hybrid Trace",
    tag: "Hybrid",
  },
  fallback_no_key_demo: {
    title: "Force Fallback Demo",
    tag: "Fallback",
  },
};

export function TeamAdminCard() {
  const { simulations, runSimulation, runRoute, loading, error, searchQuery } = useRouteIQ();
  const [prompt, setPrompt] = useState("");
  const [privacy, setPrivacy] = useState("internal");
  const [taskType, setTaskType] = useState("general");
  const [activeSimId, setActiveSimId] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt) return;
    runRoute({ prompt, task_type: taskType, privacy_level: privacy });
  };

  useEffect(() => {
    if (error) {
      const isNetworkError =
        error.toLowerCase().includes("fetch") || error.toLowerCase().includes("network");
      toast.error(isNetworkError ? "Backend Cold Start" : "Routing Error", {
        description: isNetworkError
          ? "The routing engine is waking up. Please try again in 10-15 seconds."
          : error,
        id: error,
      });
    }
  }, [error]);

  return (
    <TileCard
      title="Simulation Console"
      subtitle="Test Gemma vs Fireworks routing logic"
      tooltip="Run prompts to test RouteIQ's flow: Local Solver → Gemma Layer → Confidence Check → Fireworks Fallback. Watch how local-first saves tokens."
    >
      <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-3">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter prompt to evaluate..."
          className="min-h-[80px] w-full resize-none rounded-xl border border-border bg-canvas p-3 text-sm text-tile-fg outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/30 transition-all"
          required
        />

        <div className="flex gap-3">
          <label className="w-1/2 flex flex-col gap-1.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-tile-muted pl-1">
              Privacy Level
            </span>
            <select
              value={privacy}
              onChange={(e) => setPrivacy(e.target.value)}
              className="w-full rounded-xl border border-border bg-canvas px-3 py-2 text-sm text-tile-fg outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/30 transition-all"
            >
              <option value="public">Public</option>
              <option value="internal">Internal</option>
              <option value="confidential">Confidential</option>
              <option value="regulated">Regulated</option>
            </select>
          </label>
          <label className="w-1/2 flex flex-col gap-1.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-tile-muted pl-1">
              Task Type
            </span>
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
              className="w-full rounded-xl border border-border bg-canvas px-3 py-2 text-sm text-tile-fg outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/30 transition-all"
            >
              <option value="general">General</option>
              <option value="code">Code / Development</option>
              <option value="analytical">Data / Analytical</option>
              <option value="creative">Creative Writing</option>
            </select>
          </label>
        </div>

        <button
          disabled={loading || !prompt}
          type="submit"
          className="mt-1 flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-2.5 text-sm font-semibold text-white transition hover:bg-brand/90 disabled:opacity-50"
        >
          {loading && !activeSimId && <PiSpinner className="h-4 w-4 animate-spin" />}
          {loading && !activeSimId ? "Routing..." : "Run Route Decision"}
        </button>
      </form>

      {simulations.length > 0 && (
        <div className="mt-5 space-y-2 border-t border-border pt-4">
          <p className="pl-1 text-[10px] font-semibold uppercase tracking-widest text-tile-muted">
            Built-in Scenarios
          </p>
          <div className="flex flex-col gap-1">
            {simulations
              .filter((sim) => sim.id.toLowerCase().includes(searchQuery.toLowerCase()))
              .slice(0, 4)
              .map((sim) => {
                const meta = SCENARIO_META[sim.id] || {
                  title: sim.id,
                  tag: "Scenario",
                };
                const isRunning = activeSimId === sim.id;

                return (
                  <button
                    key={sim.id}
                    type="button"
                    disabled={loading}
                    onClick={() => {
                      setActiveSimId(sim.id);
                      runSimulation(sim.id).finally(() => setActiveSimId(null));
                    }}
                    className={`group flex items-center justify-between rounded-xl border border-transparent px-3 py-2.5 text-left transition-all ${
                      isRunning
                        ? "bg-brand-softer border-brand/20"
                        : "hover:bg-canvas hover:border-border disabled:opacity-50"
                    }`}
                  >
                    <div className="flex flex-col items-start gap-1.5 overflow-hidden">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-sm font-semibold ${isRunning ? "text-brand" : "text-tile-fg"} transition-colors`}
                        >
                          {meta.title}
                        </span>
                        <span className="rounded bg-brand-softer px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-widest text-brand">
                          {meta.tag}
                        </span>
                      </div>
                      <p className="line-clamp-1 w-full text-[11px] text-tile-muted">
                        {sim.prompt_preview || sim.id}
                      </p>
                    </div>
                    <div className="shrink-0 pl-3">
                      {isRunning ? (
                        <PiSpinner className="h-4 w-4 animate-spin text-brand" />
                      ) : (
                        <PiPlayCircle className="h-4 w-4 text-tile-muted opacity-40 transition group-hover:text-brand" />
                      )}
                    </div>
                  </button>
                );
              })}
          </div>
        </div>
      )}
    </TileCard>
  );
}
