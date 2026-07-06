import { useState } from "react";
import { TileCard } from "./TileCard";
import { useRouteIQ } from "@/hooks/use-route-iq";
import { LuPlay } from "react-icons/lu";

export function TeamAdminCard() {
  const { simulations, runSimulation, runRoute, loading, searchQuery } = useRouteIQ();
  const [prompt, setPrompt] = useState("");
  const [privacy, setPrivacy] = useState("internal");
  const [taskType, setTaskType] = useState("general");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt) return;
    runRoute({ prompt, task_type: taskType, privacy_level: privacy });
  };

  return (
    <TileCard 
      title="Simulation Console" 
      subtitle="Test AI routing logic live"
      tooltip="Run prompts against the backend routing engine to observe local vs fallback intelligence execution behavior."
    >
      <form onSubmit={handleSubmit} className="mt-3 flex flex-col gap-3">
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
          className="mt-1 flex w-full items-center justify-center rounded-xl bg-shell-2 py-2.5 text-sm font-semibold text-shell-fg transition hover:bg-shell disabled:opacity-50"
        >
          {loading ? "Routing..." : "Run Route Decision"}
        </button>
      </form>

      {simulations.length > 0 && (
        <div className="mt-5 space-y-2 border-t border-shell-muted/20 pt-4">
          <p className="text-xs font-semibold text-tile-muted">Quick Scenario Tests</p>
          <div className="grid grid-cols-2 gap-2">
            {simulations
              .filter((sim) => sim.id.toLowerCase().includes(searchQuery.toLowerCase()))
              .slice(0, 4)
              .map((sim) => (
              <button
                key={sim.id}
                type="button"
                onClick={() => runSimulation(sim.id)}
                className="flex items-center justify-between rounded-lg border border-shell-muted/30 p-2 text-left text-[10px] text-tile-fg transition hover:border-brand/40 hover:bg-brand-softer/10"
              >
                <span className="truncate">{sim.id.replace(/_/g, " ")}</span>
                <LuPlay className="shrink-0 text-brand" />
              </button>
            ))}
          </div>
        </div>
      )}
    </TileCard>
  );
}
