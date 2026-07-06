import { create } from "zustand";
import { LuLayoutGrid, LuUsers, LuUser, LuSwords } from "react-icons/lu";
import type { IconType } from "react-icons";

export type NavItem = { id: string; label: string; icon: IconType };
export type Team = { name: string; matches: number };
export type RegionSlice = { label: string; percent: number };
export type TrendPoint = { stage: string; views: number };
export type SparkPoint = { x: number; y: number };
export type Coach = { name: string; role: string; avatar: string };

type DashboardState = {
  coach: Coach;
  nav: NavItem[];
  activeNavId: string;
  setActiveNav: (id: string) => void;
  tabs: string[];
  activeTab: string;
  setActiveTab: (t: string) => void;
  regions: RegionSlice[];
  activeTeams: Team[];
  trend: TrendPoint[];
  totalTeams: number;
  totalTeamsSpark: SparkPoint[];
  registeredPlayers: number;
  completion: number;
  activeMatches: number;
  activeMatchesBars: number[];
};

export const useDashboard = create<DashboardState>((set) => ({
  coach: {
    name: "Riya Kapoor",
    role: "Coach",
    avatar: "https://i.pravatar.cc/96?img=47",
  },
  nav: [{ id: "overview", label: "Overview", icon: LuLayoutGrid }],
  activeNavId: "overview",
  setActiveNav: (id) => set({ activeNavId: id }),

  tabs: ["Compete", "Track", "Analyze", "Dominate", "Rank"],
  activeTab: "Compete",
  setActiveTab: (t) => set({ activeTab: t }),

  regions: [
    { label: "Europe", percent: 32 },
    { label: "Others", percent: 15 },
    { label: "S. Africa", percent: 12 },
    { label: "S. America", percent: 7 },
    { label: "N. America", percent: 12 },
    { label: "Asia", percent: 21 },
  ],

  activeTeams: [
    { name: "Thunder FC", matches: 28 },
    { name: "Phoenix United", matches: 26 },
    { name: "Titan Sports", matches: 24 },
    { name: "Strom Warriors", matches: 22 },
  ],

  trend: [
    { stage: "Qualifiers", views: 20000 },
    { stage: "Round 32", views: 38000 },
    { stage: "Round 16", views: 46000 },
    { stage: "Quarter Finals", views: 92000 },
    { stage: "Semi Finals", views: 138000 },
    { stage: "Finals", views: 178000 },
  ],

  totalTeams: 128,
  totalTeamsSpark: [
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
  activeMatches: 24,
  activeMatchesBars: [
    30, 55, 40, 70, 45, 85, 60, 95, 50, 75, 40, 90, 65, 80, 55, 100, 45, 70, 35, 85,
  ],
}));
