import { PiMagnifyingGlass } from "react-icons/pi";
import { ModeToggle } from "@/components/ui/mode-toggle";
import { useRouteIQ } from "@/hooks/use-route-iq";

export function TopBar() {
  const { searchQuery, setSearchQuery, status, error } = useRouteIQ();

  return (
    <header className="flex flex-col md:flex-row md:items-start justify-between gap-6 px-1">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-shell-fg">
          OmniEdge RouteIQ Dashboard
        </h1>
        <p className="mt-1 text-xs text-shell-fg/70">
          Monitor and simulate AI routing intelligence in real-time.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <label className="flex flex-1 md:flex-initial items-center gap-2 rounded-full bg-white/15 px-4 py-2 text-xs text-shell-fg/80 backdrop-blur-sm ring-1 ring-white/10 focus-within:ring-white/30 transition">
          <PiMagnifyingGlass size={14} className="opacity-70 shrink-0" />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search scenarios..."
            className="w-full md:w-32 lg:w-44 bg-transparent outline-none placeholder:text-shell-fg/60"
          />
        </label>

        <div
          className="flex items-center gap-2 rounded-full border border-shell-muted/20 bg-shell p-2 px-3 text-[10px] font-bold uppercase tracking-wider text-shell-fg shadow-sm transition-colors"
          title={
            error
              ? "Backend is offline or cold-starting."
              : status
                ? "Backend is online."
                : "Connecting to backend..."
          }
        >
          {status && !error ? (
            <div className="h-2 w-2 shrink-0 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
          ) : error ? (
            <div className="h-2 w-2 shrink-0 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
          ) : (
            <div className="h-2 w-2 shrink-0 rounded-full bg-amber-500 animate-pulse shadow-[0_0_8px_rgba(245,158,11,0.8)]" />
          )}
          <span className="hidden sm:inline">
            {status && !error ? "Engine Online" : error ? "Engine Offline" : "Connecting..."}
          </span>
        </div>

        <ModeToggle />
      </div>
    </header>
  );
}
