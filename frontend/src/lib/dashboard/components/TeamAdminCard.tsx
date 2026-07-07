import { useState, useEffect } from "react";
import { TileCard } from "./TileCard";
import { toast } from "sonner";
import { useRouteIQ } from "@/hooks/use-route-iq";
import { LuPlay } from "react-icons/lu";
import { Loader2, AlertCircle } from "lucide-react";

const SCENARIO_META: Record<string, { title: string; tag: string; color: string }> = {
  local_sensitive_prompt: { 
    title: "Privacy-first Local", 
    tag: "Local", 
    color: "text-emerald-500" 
  },
  cloud_complex_architecture: { 
    title: "Cloud Architecture", 
    tag: "Cloud", 
    color: "text-blue-500" 
  },
  hybrid_confidential_code: { 
    title: "Hybrid Confidential", 
    tag: "Hybrid", 
    color: "text-purple-500" 
  },
  fallback_no_key_demo: { 
    title: "Fallback Demo", 
    tag: "Fallback", 
    color: "text-amber-500" 
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
      const isNetworkError = error.toLowerCase().includes("fetch") || error.toLowerCase().includes("network");
      toast.error(isNetworkError ? "Backend Cold Start" : "Routing Error", {
        description: isNetworkError
          ? "The routing engine is waking up. Please try again in 10-15 seconds."
          : "Unable to complete route decision. Please check backend connection.",
        id: error,
      });
    }
  }, [error]);

  return (
    <TileCard
      title="Simulation Console"
      subtitle="Test AI routing logic live"
      tooltip="Run prompts against the backend routing engine to observe local vs fallback intelligence execution behavior."
    >
      <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-3">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter prompt to evaluate..."
          className="min-h-[80px] w-full resize-none rounded-xl border border-shell-muted/30 bg-slate-50 p-3 text-sm text-tile-fg outline-none focus:border-brand/40 dark:bg-slate-900"
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
              className="w-full rounded-xl border border-shell-muted/30 bg-slate-50 px-3 py-2 text-sm text-tile-fg outline-none focus:border-brand/40 transition-colors dark:bg-slate-900"
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
              className="w-full rounded-xl border border-shell-muted/30 bg-slate-50 px-3 py-2 text-sm text-tile-fg outline-none focus:border-brand/40 transition-colors dark:bg-slate-900"
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
          className="mt-1 flex w-full items-center justify-center gap-2 rounded-xl bg-shell-2 py-2.5 text-sm font-semibold text-shell-fg transition hover:bg-shell disabled:opacity-50"
        >
          {loading && !activeSimId && <Loader2 className="animate-spin" />}
          {loading && !activeSimId ? "Routing..." : "Run Route Decision"}
        </button>
      </form>

      {simulations.length > 0 && (
        <div className="mt-5 space-y-2 border-t border-shell-muted/20 pt-4">
          <p className="pl-1 text-[10px] font-semibold uppercase tracking-widest text-tile-muted">
            Built-in Scenarios
          </p>
          <div className="flex flex-col">
            {simulations
              .filter((sim) => sim.id.toLowerCase().includes(searchQuery.toLowerCase()))
              .slice(0, 4)
              .map((sim) => {
                const meta = SCENARIO_META[sim.id] || { 
                  title: sim.id, 
                  tag: "Scenario", 
                  color: "text-shell-muted" 
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
                    className={`group flex items-center justify-between rounded-lg px-2 py-2 text-left transition ${
                      isRunning 
                        ? "bg-black/5 dark:bg-white/5" 
                        : "hover:bg-black/5 dark:hover:bg-white/5 disabled:opacity-50"
                    }`}
                  >
                    <div className="flex flex-col items-start gap-1 overflow-hidden">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-tile-fg">{meta.title}</span>
                        <span className={`text-[10px] font-bold uppercase tracking-widest ${meta.color}`}>
                          {meta.tag}
                        </span>
                      </div>
                      <p className="line-clamp-1 w-full text-[10px] text-tile-muted">
                        {sim.prompt_preview || sim.id}
                      </p>
                    </div>
                    <div className="shrink-0 pl-3">
                      {isRunning ? (
                        <Loader2 className="h-4 w-4 animate-spin text-brand" />
                      ) : (
                        <LuPlay className="h-4 w-4 text-tile-muted opacity-60 transition group-hover:text-brand group-hover:opacity-100" />
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
