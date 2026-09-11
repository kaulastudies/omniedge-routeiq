import { create } from "zustand";
import { PiSquaresFour, PiUsers, PiUser, PiSword } from "react-icons/pi";
import type { IconType } from "react-icons";

export type NavItem = { id: string; label: string; icon: IconType };
export type Provider = { name: string; executions: number };
export type RegionSlice = { label: string; percent: number };
export type TrendPoint = { stage: string; views: number };
export type SparkPoint = { x: number; y: number };
export type SystemAdmin = { name: string; role: string; avatar: string };

type DashboardState = {
  admin: SystemAdmin;
  nav: NavItem[];
  activeNavId: string;
  setActiveNav: (id: string) => void;
  tabs: string[];
  activeTab: string;
  setActiveTab: (t: string) => void;
  regions: RegionSlice[];
  activeProviders: Provider[];
  trend: TrendPoint[];
  totalRoutes: number;
  totalRoutesSpark: SparkPoint[];
  registeredPlayers: number;
  completion: number;
  activeExecutions: number;
  activeExecutionsBars: number[];
};

export const useDashboard = create<DashboardState>((set) => ({
  admin: {
    name: "RouteIQ Admin",
    role: "System",
    avatar: "https://i.pravatar.cc/96?img=47",
  },
  nav: [{ id: "overview", label: "Overview", icon: PiSquaresFour }],
  activeNavId: "overview",
  setActiveNav: (id) => set({ activeNavId: id }),

  tabs: ["Simulation Console", "Routing", "Provider Health", "Audit Timeline", "Token Savings"],
  activeTab: "Simulation Console",
  setActiveTab: (t) => set({ activeTab: t }),

  regions: [
    { label: "Europe", percent: 32 },
    { label: "Others", percent: 15 },
    { label: "S. Africa", percent: 12 },
    { label: "S. America", percent: 7 },
    { label: "N. America", percent: 12 },
    { label: "Asia", percent: 21 },
  ],

  activeProviders: [
    { name: "Local", executions: 28 },
    { name: "Cloud", executions: 26 },
    { name: "Hybrid", executions: 24 },
    { name: "Fallback", executions: 22 },
  ],

  trend: [
    { stage: "Received", views: 20000 },
    { stage: "Classified", views: 38000 },
    { stage: "Routed", views: 46000 },
    { stage: "Provider Select", views: 92000 },
    { stage: "Executed", views: 138000 },
    { stage: "Logged", views: 178000 },
  ],

  totalRoutes: 128,
  totalRoutesSpark: [
    { x: 0, y: 40 },
    { x: 1, y: 55 },
    { x: 2, y: 30 },
    { x: 3, y: 68 },
    { x: 4, y: 45 },
    { x: 5, y: 78 },
    { x: 6, y: 52 },
    { x: 7, y: 90 },
    { x: 8, y: 60 },
    { x: 9, y: 72 },
  ],

  registeredPlayers: 1500,
  completion: 68,
  activeExecutions: 24,
  activeExecutionsBars: [
    30, 55, 40, 70, 45, 85, 60, 95, 50, 75, 40, 90, 65, 80, 55, 100, 45, 70, 35, 85,
  ],
}));
