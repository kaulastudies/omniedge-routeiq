"use client";

import { Activity, Cpu, Network, ShieldAlert } from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-[#0A0A0A] text-white font-sans overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-[#262626] bg-[#0A0A0A] flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-blue-500/20 flex items-center justify-center border border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
            <Cpu className="w-4 h-4 text-blue-500" />
          </div>
          <span className="font-bold tracking-tight text-lg">OmniEdge</span>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          <button className="relative w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-white bg-[#171717]">
            <Activity className="w-4 h-4" />
            Command Nexus
            <div className="absolute left-0 w-1 h-5 bg-blue-500 rounded-r-full" />
          </button>
          <button className="relative w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-[#A3A3A3] hover:text-white hover:bg-[#171717]/50 transition-colors">
            <Cpu className="w-4 h-4" /> Model Config
          </button>
          <button className="relative w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-[#A3A3A3] hover:text-white hover:bg-[#171717]/50 transition-colors">
            <ShieldAlert className="w-4 h-4" /> Audit Logs
          </button>
        </nav>
        
        <div className="p-4 border-t border-[#262626]">
          <div className="flex items-center gap-3 px-3 py-2 text-xs text-[#A3A3A3] font-medium bg-[#171717]/30 rounded-lg border border-[#262626]/50">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
            Edge Node: Online
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative bg-[#0A0A0A]">
        <header className="h-16 border-b border-[#262626] bg-[#0A0A0A]/80 backdrop-blur-md flex items-center px-8 z-10">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-[#A3A3A3]">RouteIQ</span>
            <span className="text-[#A3A3A3]">/</span>
            <span className="text-white font-medium">Core Execution</span>
          </div>
        </header>
        <div className="flex-1 overflow-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
