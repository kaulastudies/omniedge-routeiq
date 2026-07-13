import { TileCard } from "./TileCard";
import { useRouteIQ } from "@/hooks/use-route-iq";
import { PiActivity, PiCheckCircle, PiXCircle } from "react-icons/pi";
import { Skeleton } from "@/components/ui/skeleton";

export function CourtCard() {
  const status = useRouteIQ((s) => s.status);

  return (
    <TileCard
      title="System Health"
      subtitle="Model providers connectivity"
      tooltip="Real-time heartbeat monitor connecting directly to AI providers. Automatically fails over dependencies when nodes go offline to maintain throughput."
    >
      <div className="mt-4 flex flex-col gap-3">
        {!status ? (
          <div className="space-y-4">
            <Skeleton className="h-16 w-full rounded-xl" />
            <div className="space-y-3 pt-2">
              <Skeleton className="h-4 w-28" />
              <div className="space-y-2">
                <Skeleton className="h-8 w-full rounded-lg" />
                <Skeleton className="h-8 w-full rounded-lg" />
                <Skeleton className="h-8 w-full rounded-lg" />
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-3 rounded-xl border border-shell-muted/20 bg-canvas p-3">
              <PiActivity className="text-brand text-[22px]" />
              <div className="flex-1">
                <p className="text-xs font-semibold text-tile-fg">Router Engine</p>
                <p className="text-[10px] text-tile-muted">
                  v{status.version} • {status.environment}
                </p>
              </div>
              <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-500 uppercase">
                {status.status}
              </span>
            </div>

            <div className="space-y-2">
              <p className="text-[10px] font-semibold text-tile-muted uppercase tracking-widest pl-1">
                Connected Providers
              </p>
              {status.providers.map((p) => (
                <div
                  key={p.name}
                  className="flex items-center justify-between rounded-lg px-2 py-1.5 hover:bg-white/5 transition"
                >
                  <div className="flex items-center gap-2">
                    {p.available ? (
                      <PiCheckCircle className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <PiXCircle className="h-4 w-4 text-rose-500" />
                    )}
                    <span className="text-sm text-tile-fg font-medium capitalize">{p.name}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-tile-muted font-mono tabular-nums">
                      {p.latency_ms !== null ? `${p.latency_ms}ms` : "-"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </TileCard>
  );
}
