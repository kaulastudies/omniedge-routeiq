"use client";

import { useEffect } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { HeroCard } from "./HeroCard";
import { CourtCard } from "./CourtCard";
import { TeamAdminCard } from "./TeamAdminCard";
import { MostActiveTeamsCard } from "./MostActiveTeamsCard";
import { LiveViewsCard } from "./LiveViewsCard";
import { TotalTeamsCard, RegisteredCard, CompletionCard, ActiveMatchesCard } from "./StatCards";
import { Logo } from "./Logo";
import { useRouteIQ } from "@/hooks/use-route-iq";

export function DashboardShell({ children }: { children?: React.ReactNode }) {
  const refreshData = useRouteIQ((state) => state.refreshData);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  return (
    <div className="min-h-screen w-full bg-transparent flex flex-col">
      {/* Distinct "Hardware Panel" shell layout */}
      <div className="shell-gradient flex-1 flex flex-col relative w-full overflow-hidden shadow-2xl shadow-slate-950/60 ring-1 ring-white/10 before:absolute before:inset-0 before:pointer-events-none before:bg-[radial-gradient(ellipse_at_center,var(--color-brand-softer)_0%,transparent_70%)] before:opacity-[0.03]">
        <div className="flex flex-1 flex-col lg:flex-row">
          {/* Thick Hardware Rail (Sidebar) */}
          <aside className="relative flex lg:h-auto lg:w-20 w-full shrink-0 flex-row lg:flex-col items-center justify-between lg:justify-start gap-4 lg:gap-8 border-b lg:border-b-0 lg:border-r border-shell-muted/10 bg-black/20 p-4 lg:py-8 text-shell-fg backdrop-blur-md">
            <div className="grid h-12 w-12 place-items-center rounded-xl bg-gradient-to-b from-white/20 to-white/5 shadow-inner ring-1 ring-white/10">
              <Logo size={24} color="currentColor" />
            </div>
            <Sidebar />
          </aside>

          {/* Main Console Content */}
          <div className="flex-1 space-y-6 px-4 py-6 md:px-8 md:py-8 lg:px-12 lg:py-10">
            <TopBar />

            {children ? (
              children
            ) : (
              <>
                {/* Row 1: Hero | Court | TeamAdmin */}
                <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
                  <div className="lg:col-span-5">
                    <HeroCard />
                  </div>
                  <div className="lg:col-span-3">
                    <CourtCard />
                  </div>
                  <div className="lg:col-span-4">
                    <TeamAdminCard />
                  </div>
                </div>

                {/* Row 2: LiveViews (left, spans 2 cols) | MostActive | 4 stat tiles (2x2) */}
                <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
                  <div className="lg:col-span-5">
                    <LiveViewsCard />
                  </div>
                  <div className="lg:col-span-3">
                    <MostActiveTeamsCard />
                  </div>
                  <div className="grid grid-cols-2 gap-4 lg:col-span-4">
                    <TotalTeamsCard />
                    <RegisteredCard />
                    <CompletionCard />
                    <ActiveMatchesCard />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
