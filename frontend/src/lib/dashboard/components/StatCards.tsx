import { Area, AreaChart, BarChart, Bar, ResponsiveContainer } from "recharts";
import {
  LuUser,
  LuCircleDot,
  LuActivity,
  LuRoute,
  LuZap,
  LuClock,
  LuTriangleAlert,
} from "react-icons/lu";
import { TileCard } from "./TileCard";
import { useRouteIQ } from "@/hooks/use-route-iq";
import { Skeleton } from "@/components/ui/skeleton";

/* --- Total Routes: sparkline with pill callout ------------------- */
export function TotalTeamsCard() {
  const metrics = useRouteIQ((s) => s.metrics);
  const totalRoutes = metrics?.total_requests || 0;

  // Dummy spark data for visual parity
  const totalTeamsSpark = [
    { x: 0, y: 40 },
    { x: 1, y: 55 },
    { x: 2, y: 30 },
    { x: 3, y: 68 },
    { x: 4, y: 45 },
    { x: 5, y: 78 },
    { x: 6, y: 52 },
    { x: 7, y: 90 },
    { x: 8, y: 60 },
    { x: 9, y: totalRoutes },
  ];

  return (
    <TileCard title="Total Routes" icon={LuRoute} action="icon">
      {!metrics ? (
        <div className="mt-2 space-y-3">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="mt-2 h-16 w-full" />
        </div>
      ) : (
        <>
          <div className="mt-2 text-3xl font-semibold tracking-tight tabular-nums">
            {totalRoutes}
          </div>
          <div className="relative mt-2 h-16">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={totalTeamsSpark} margin={{ top: 6, right: 4, left: 4, bottom: 0 }}>
                <defs>
                  <linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-brand)" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="var(--color-brand)" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="y"
                  stroke="var(--color-brand)"
                  strokeWidth={1.8}
                  fill="url(#sparkFill)"
                />
              </AreaChart>
            </ResponsiveContainer>
            <span className="absolute right-2 top-0 rounded-md bg-black px-1.5 py-0.5 text-[10px] font-semibold text-white">
              {totalRoutes}
            </span>
          </div>
        </>
      )}
    </TileCard>
  );
}

/* --- Token Savings: half-gauge --------------------------------------- */
export function RegisteredCard() {
  const metrics = useRouteIQ((s) => s.metrics);
  const savings = metrics?.estimated_token_savings_usd || 0;

  const ticks = 32;
  const cx = 90;
  const cy = 78;
  const inner = 40;
  const outer = 60;

  return (
    <TileCard
      title="Token Savings"
      icon={LuZap}
      action="icon"
      tooltip="Theoretical token calculation showing expected compute expenses successfully diverted away from costly cloud models."
    >
      {!metrics ? (
        <div className="mt-2 space-y-3">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="mt-1 h-20 w-full" />
        </div>
      ) : (
        <>
          <div className="mt-1 text-3xl font-semibold tracking-tight tabular-nums">
            ${savings.toFixed(3)}
          </div>
          <div className="relative mt-1 flex justify-center">
            <svg viewBox="0 0 180 90" className="h-20 w-full max-w-[180px]">
              {Array.from({ length: ticks }).map((_, i) => {
                const angle = Math.PI * (i / (ticks - 1)) + Math.PI;
                const x1 = cx + Math.cos(angle) * inner;
                const y1 = cy + Math.sin(angle) * inner;
                const x2 = cx + Math.cos(angle) * outer;
                const y2 = cy + Math.sin(angle) * outer;
                const isActive = i < ticks * 0.75;
                return (
                  <line
                    key={i}
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke={isActive ? "var(--color-brand)" : "var(--color-brand-softer)"}
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                );
              })}
            </svg>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center">
              <div className="text-[10px] text-tile-muted">Saved (USD)</div>
            </div>
          </div>
        </>
      )}
    </TileCard>
  );
}

/* --- Avg Latency: diagonal-hatched progress bar -------------------- */
export function CompletionCard() {
  const metrics = useRouteIQ((s) => s.metrics);
  const latency = Math.round(metrics?.avg_latency_ms || 0);
  const pct = Math.min(100, Math.max(0, latency / 40));

  return (
    <TileCard title="Avg Latency" icon={LuClock} action="icon">
      {!metrics ? (
        <div className="mt-2 space-y-3">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="mt-6 h-6 w-full rounded-md" />
        </div>
      ) : (
        <>
          <div className="mt-1 text-3xl font-semibold tracking-tight tabular-nums">{latency}ms</div>
          <div className="mt-6 h-6 w-full overflow-hidden rounded-md bg-brand-softer">
            <svg width="0" height="0" className="absolute">
              <defs>
                <pattern
                  id="hatch"
                  patternUnits="userSpaceOnUse"
                  width="6"
                  height="6"
                  patternTransform="rotate(45)"
                >
                  <rect width="3" height="6" fill="var(--color-brand)" />
                  <rect x="3" width="3" height="6" fill="oklch(0.7 0.2 25)" />
                </pattern>
              </defs>
            </svg>
            <div
              className="h-full"
              style={{
                width: `${pct}%`,
                background: "url(#hatch)",
                backgroundColor: "var(--color-brand)",
                backgroundImage:
                  "repeating-linear-gradient(45deg, oklch(0.6 0.22 25) 0 3px, oklch(0.72 0.2 22) 3px 6px)",
              }}
            />
          </div>
        </>
      )}
    </TileCard>
  );
}

/* --- Fallbacks: variable bar chart -------------------------- */
export function ActiveMatchesCard() {
  const metrics = useRouteIQ((s) => s.metrics);
  const fallbacks = metrics?.fallback_count || 0;

  // Dummy chart details
  const activeMatchesBars = [
    30,
    55,
    40,
    70,
    45,
    85,
    60,
    95,
    50,
    75,
    40,
    90,
    65,
    80,
    55,
    100,
    45,
    70,
    35,
    Math.max(10, fallbacks * 10),
  ];

  const data = activeMatchesBars.map((v, i) => ({ i, v }));
  return (
    <TileCard
      title="Fallbacks"
      icon={LuTriangleAlert}
      action="icon"
      tooltip="A reliability guard metric noting how many requests were safely intercepted and routed to a redundant backup engine due to an outage or rate limit."
    >
      {!metrics ? (
        <div className="mt-2 space-y-3">
          <Skeleton className="h-8 w-16" />
          <Skeleton className="mt-3 h-16 w-full" />
        </div>
      ) : (
        <>
          <div className="mt-1 text-3xl font-semibold tracking-tight tabular-nums">{fallbacks}</div>
          <div className="mt-3 h-16 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} barCategoryGap={2}>
                <Bar dataKey="v" fill="var(--color-brand)" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </TileCard>
  );
}
