"use client";

import { DashboardShell } from "@/lib/dashboard/components";

export default function Page() {
  return (
    <div className="relative min-h-screen">
      <DashboardShell />
      
      {/* Hackathon Branding Footer - Minimalist Linear/Vercel Style */}
      <div className="pointer-events-none fixed bottom-3 right-6 z-50 flex items-center gap-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-shell-muted/40 mix-blend-plus-lighter">
        <span>AMD ACT II Hackathon</span>
        <span className="opacity-40">•</span>
        <span>Rama Chandra</span>
        <span className="opacity-40">•</span>
        <span>Nabothan</span>
        <span className="opacity-40">•</span>
        <span>Rameen</span>
      </div>
    </div>
  );
}
