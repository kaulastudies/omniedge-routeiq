"use client";

import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { useRouteIQ } from "@/hooks/use-route-iq";
import { PiArrowRight } from "react-icons/pi";

import { InfoTooltip } from "./InfoTooltip";

export function HeroCard() {
  const { routeResult: result, loading } = useRouteIQ();
  const activeDecision = result?.decision?.target || "waiting";
  const provider = result?.provider_response?.provider || "not routed";
  const confidence = result?.decision?.confidence || 0;

  return (
    <div className="relative flex h-full min-h-[400px] flex-col justify-between overflow-hidden rounded-[24px] bg-gradient-to-br from-shell-gray/20 to-black/60 shadow-inner ring-1 ring-white/5">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-shell-2/90 via-shell-2/40 to-transparent" />

      {/* Dynamic Aura Glow based on Routing Target */}
      <div
        className={cn(
          "pointer-events-none absolute -right-32 -top-32 h-96 w-96 rounded-full mix-blend-screen blur-[100px] transition-all duration-1000",
          provider === "not routed"
            ? "bg-transparent"
            : result?.fallback_used
              ? "bg-amber-500/20"
              : activeDecision === "local"
                ? "bg-emerald-500/20"
                : "bg-sky-500/20",
        )}
      />

      <div className="relative z-10 p-6 flex flex-col justify-between h-full">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-3xl font-semibold tracking-tight text-shell-fg drop-shadow-md">
              Route Decision
            </h2>
            <InfoTooltip content="Visual breakdown of the final intelligence routing path, highlighting whether Gemma solved it locally or if it fell back to Fireworks." />
          </div>
          <p className="mt-1 text-sm text-shell-muted">
            Local Gemma layer vs Fireworks fallback outcome.
          </p>
        </div>

        {loading ? (
          <div className="mt-auto space-y-4">
            <div className="flex items-center gap-3">
              <Skeleton className="h-6 w-16 rounded-full opacity-50" />
              <Skeleton className="h-5 w-32 opacity-50" />
            </div>
            <Skeleton className="h-12 w-full rounded-lg opacity-40" />
            <div className="mt-4 grid grid-cols-3 gap-3">
              <Skeleton className="h-[68px] w-full rounded-xl opacity-30" />
              <Skeleton className="h-[68px] w-full rounded-xl opacity-30" />
              <Skeleton className="h-[68px] w-full rounded-xl opacity-30" />
            </div>
          </div>
        ) : (
          <div className="mt-auto space-y-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-medium flex-wrap">
                {provider === "not routed" ? (
                  <span className="rounded-full bg-shell-muted/10 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-shell-fg/40 ring-1 ring-white/5">
                    Awaiting Execution
                  </span>
                ) : (
                  <>
                    <span className="text-shell-fg/60">Task</span>
                    <PiArrowRight className="h-4 w-4 shrink-0 text-shell-muted" />

                    {activeDecision === "cloud" && !result?.fallback_used ? (
                      <span className="rounded-full bg-sky-300 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-shell-2 shadow drop-shadow-sm">
                        Fireworks (Direct)
                      </span>
                    ) : (
                      <>
                        <span
                          className={cn(
                            "rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-wider shadow drop-shadow-sm transition-all",
                            result?.fallback_used
                              ? "bg-shell-muted/20 text-shell-fg/60 line-through ring-1 ring-white/10"
                              : "bg-emerald-400 text-shell-2",
                          )}
                        >
                          Gemma Layer
                        </span>

                        {result?.fallback_used ? (
                          <>
                            <PiArrowRight className="h-4 w-4 shrink-0 text-amber-500/70" />
                            <span className="rounded-full bg-amber-400 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-shell-2 shadow drop-shadow-sm">
                              Fireworks Fallback
                            </span>
                          </>
                        ) : (
                          <>
                            <PiArrowRight className="h-4 w-4 shrink-0 text-emerald-500/70" />
                            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                              ✓ {Math.round(confidence * 100)}% Conf
                            </span>
                          </>
                        )}
                      </>
                    )}
                  </>
                )}
              </div>

              <p className="text-[16px] leading-relaxed text-shell-fg/90">
                {result?.decision?.decision_summary ||
                  "Run a generic task to generate an explainable routing decision."}
              </p>
            </div>

            {/* Performance Metrics Section */}
            {provider !== "not routed" && (
              <div className="grid grid-cols-3 gap-3 border-t border-shell-muted/10 pt-5">
                <div className="group flex flex-col justify-center gap-1 rounded-xl bg-black/20 p-3 backdrop-blur-md ring-1 ring-white/5 transition-all hover:bg-black/40 hover:ring-white/10">
                  <span className="text-[9px] font-bold uppercase tracking-widest text-shell-muted/80">
                    Execution
                  </span>
                  <span className="font-mono text-lg font-light text-shell-fg tracking-tight">
                    {result?.latency_ms}
                    <span className="ml-0.5 font-sans text-xs text-shell-muted">ms</span>
                  </span>
                </div>
                <div className="group flex flex-col justify-center gap-1 rounded-xl bg-black/20 p-3 backdrop-blur-md ring-1 ring-white/5 transition-all hover:bg-black/40 hover:ring-white/10">
                  <span className="text-[9px] font-bold uppercase tracking-widest text-shell-muted/80">
                    Tokens
                  </span>
                  <span className="font-mono text-lg font-light text-shell-fg tracking-tight">
                    {result?.provider_response?.total_tokens || 0}
                  </span>
                </div>
                <div className="group flex flex-col justify-center gap-1 rounded-xl bg-black/20 p-3 backdrop-blur-md ring-1 ring-white/5 transition-all hover:bg-black/40 hover:ring-white/10">
                  <span className="text-[9px] font-bold uppercase tracking-widest text-shell-muted/80">
                    Savings
                  </span>
                  <span className="font-mono text-lg font-medium text-emerald-400 tracking-tight drop-shadow-sm">
                    ${(result?.token_savings_estimate_usd || 0).toFixed(4)}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
