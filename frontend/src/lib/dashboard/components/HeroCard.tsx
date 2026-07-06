"use client";

import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { useRouteIQ } from "@/hooks/use-route-iq";

import { InfoTooltip } from "./InfoTooltip";

export function HeroCard() {
  const { routeResult: result, loading } = useRouteIQ();
  const activeDecision = result?.decision?.target || "waiting";
  const provider = result?.provider_response?.provider || "not routed";
  const confidence = result?.decision?.confidence || 0;

  return (
    <div className="relative flex h-full min-h-[400px] flex-col justify-between overflow-hidden rounded-[24px] bg-gradient-to-br from-shell-gray/20 to-black/60 shadow-inner">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-shell-2/90 via-shell-2/40 to-transparent" />

      <div className="relative z-10 p-6 flex flex-col justify-between h-full">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-3xl font-semibold tracking-tight text-shell-fg drop-shadow-md">
              Route Decision
            </h2>
            <InfoTooltip content="Visual breakdown of the final intelligence routing path, highlighting provider selection explicitly mapped against heuristic threshold logic." />
          </div>
          <p className="mt-1 text-sm text-shell-muted">Explainable routing outcome.</p>
        </div>

        {loading ? (
          <div className="mt-auto space-y-4">
            <div className="flex items-center gap-3">
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-6 w-16 rounded-full" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-20 w-full rounded-2xl" />
              <Skeleton className="h-20 w-full rounded-2xl" />
            </div>
            <Skeleton className="h-16 w-full rounded-2xl" />
          </div>
        ) : (
          <div className="mt-auto space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-shell-fg/80">Selected path:</span>
              <span
                className={cn(
                  "rounded-full px-4 py-1 text-xs font-bold uppercase tracking-wider text-shell-2 shadow drop-shadow-sm",
                  activeDecision === "local"
                    ? "bg-emerald-300"
                    : activeDecision === "cloud"
                      ? "bg-sky-300"
                      : activeDecision === "hybrid"
                        ? "bg-amber-300"
                        : "bg-white/90",
                )}
              >
                {activeDecision}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-2xl border border-white/20 bg-black/20 p-4 backdrop-blur-sm">
                <p className="text-xs text-shell-muted">Provider</p>
                <p className="mt-1 text-xl font-bold text-shell-fg">{provider}</p>
              </div>
              <div className="rounded-2xl border border-white/20 bg-black/20 p-4 backdrop-blur-sm">
                <p className="text-xs text-shell-muted">Confidence</p>
                <p className="mt-1 text-xl font-bold text-shell-fg">
                  {Math.round(confidence * 100)}%
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-black/20 p-4 backdrop-blur-sm">
              <p className="text-sm text-shell-fg italic">
                {result?.decision?.decision_summary ||
                  "Run a generic task to generate an explainable routing decision."}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
