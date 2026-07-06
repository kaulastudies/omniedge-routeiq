import { TileCard } from "./TileCard";
import { useRouteIQ } from "@/hooks/use-route-iq";
import { LuCheck, LuClock } from "react-icons/lu";
import { format } from "date-fns";
import { Skeleton } from "@/components/ui/skeleton";

export function LiveViewsCard() {
  const { routeResult: result, loading } = useRouteIQ();
  const timeline = result?.audit_timeline || [];

  return (
    <TileCard
      title="Audit Timeline"
      subtitle="Routing step execution trace"
      tooltip="Chronological pipeline trace for the last executed AI routing decision. Highlights security guardrails, task classification phases, provider resolution, and execution timelines."
    >
      <div className="mt-4 flex h-56 w-full flex-col overflow-y-auto pr-2">
        {loading ? (
          <div className="space-y-6 ml-3 border-l border-brand-softer/50 pb-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="relative pl-6">
                <span className="absolute -left-[11px] top-1 flex h-5 w-5 items-center justify-center rounded-full bg-canvas ring-4 ring-canvas">
                  <Skeleton className="h-4 w-4 rounded-full" />
                </span>
                <div className="flex flex-col gap-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-full" />
                </div>
              </div>
            ))}
          </div>
        ) : timeline.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-tile-muted">
            <LuClock className="mb-2 text-2xl opacity-50" />
            <p className="text-sm">Run a decision to view audit timeline</p>
          </div>
        ) : (
          <div className="relative border-l border-brand-softer/50 ml-3 space-y-6 pb-4">
            {timeline.map((event, idx) => (
              <div key={idx} className="relative pl-6">
                <span className="absolute -left-[11px] top-1 flex h-5 w-5 items-center justify-center rounded-full bg-canvas ring-4 ring-canvas">
                  <LuCheck className="h-4 w-4 text-brand" />
                </span>
                <div className="flex flex-col">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-semibold text-tile-fg uppercase tracking-wide text-xs">
                      {event.stage}
                    </span>
                    <span className="text-xs text-tile-muted tabular-nums">
                      {format(new Date(event.created_at), "HH:mm:ss.SSS")}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-tile-fg/80">{event.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </TileCard>
  );
}
