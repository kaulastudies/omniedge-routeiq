import { TileCard } from "./TileCard";
import { useRouteIQ } from "@/hooks/use-route-iq";
import { Skeleton } from "@/components/ui/skeleton";

export function MostActiveTeamsCard() {
  const metrics = useRouteIQ((s) => s.metrics);
  const splits = metrics?.provider_split_percent || { local: 0, cloud: 0, hybrid: 0 };

  const items = [
    { name: "Local", pct: splits.local },
    { name: "Cloud", pct: splits.cloud },
    { name: "Hybrid", pct: splits.hybrid },
  ];

  return (
    <TileCard
      title="Provider Split"
      subtitle="Execution traffic distribution"
      tooltip="Real-time distribution ratio mapping hybrid cloud escalations versus local private edge executions over the current session."
    >
      <ul className="mt-4 space-y-4">
        {!metrics ? (
          <>
            {[1, 2, 3].map((i) => (
              <li key={i} className="space-y-3">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-4 w-12" />
                  <Skeleton className="h-4 w-8" />
                </div>
                <Skeleton className="h-1.5 w-full rounded-full" />
              </li>
            ))}
          </>
        ) : (
          items.map((t) => {
            return (
              <li key={t.name} className="space-y-2">
                <div className="flex items-baseline justify-between">
                  <span className="text-sm font-medium text-tile-fg">{t.name}</span>
                  <span className="text-sm font-semibold text-tile-fg tabular-nums">
                    {Math.round(t.pct)}%
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-brand-softer">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand-soft to-brand"
                    style={{ width: `${Math.min(100, Math.max(0, t.pct))}%` }}
                  />
                </div>
              </li>
            );
          })
        )}
      </ul>
    </TileCard>
  );
}
