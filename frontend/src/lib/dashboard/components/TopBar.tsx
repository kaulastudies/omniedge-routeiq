import { LuSearch } from "react-icons/lu";
import { ModeToggle } from "@/components/ui/mode-toggle";
import { useRouteIQ } from "@/hooks/use-route-iq";

export function TopBar() {
  const searchQuery = useRouteIQ((s) => s.searchQuery);
  const setSearchQuery = useRouteIQ((s) => s.setSearchQuery);

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
          <LuSearch size={14} className="opacity-70 shrink-0" />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search scenarios..."
            className="w-full md:w-32 lg:w-44 bg-transparent outline-none placeholder:text-shell-fg/60"
          />
        </label>

        <ModeToggle />
      </div>
    </header>
  );
}
