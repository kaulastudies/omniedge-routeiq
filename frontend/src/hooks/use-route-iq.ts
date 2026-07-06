import { create } from "zustand";
import { RouteIQApi } from "../lib/api/client";
import {
  MetricsResponse,
  RouteRequestParams,
  RouteResponse,
  Simulation,
  StatusResponse,
} from "../lib/api/types";

interface RouteIQState {
  status: StatusResponse | null;
  metrics: MetricsResponse | null;
  simulations: Simulation[];
  routeResult: RouteResponse | null;
  loading: boolean;
  error: string | null;
  searchQuery: string;

  setSearchQuery: (query: string) => void;
  refreshData: () => Promise<void>;
  runRoute: (params: RouteRequestParams) => Promise<void>;
  runSimulation: (id: string) => Promise<void>;
}

export const useRouteIQ = create<RouteIQState>((set) => ({
  status: null,
  metrics: null,
  simulations: [],
  routeResult: null,
  loading: false,
  error: null,
  searchQuery: "",

  setSearchQuery: (q) => set({ searchQuery: q }),

  refreshData: async () => {
    try {
      const [status, metrics, simRes] = await Promise.all([
        RouteIQApi.getStatus().catch(() => null),
        RouteIQApi.getMetrics().catch(() => null),
        RouteIQApi.getSimulations().catch(() => ({ scenarios: [] })),
      ]);

      set((state) => ({
        status: status || state.status,
        metrics: metrics || state.metrics,
        simulations: simRes.scenarios || state.simulations,
      }));
    } catch (e) {
      set({ error: e instanceof Error ? e.message : "Failed to refresh data" });
    }
  },

  runRoute: async (params: RouteRequestParams) => {
    set({ loading: true, error: null });
    try {
      const result = await RouteIQApi.runRoute(params);
      set({ routeResult: result });

      // Auto-refresh metrics to reflect new route
      const metrics = await RouteIQApi.getMetrics().catch(() => null);
      if (metrics) set({ metrics });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : "Failed to run route" });
    } finally {
      set({ loading: false });
    }
  },

  runSimulation: async (id: string) => {
    set({ loading: true, error: null });
    try {
      const result = await RouteIQApi.runSimulation(id);
      set({ routeResult: result });

      // Auto-refresh metrics
      const metrics = await RouteIQApi.getMetrics().catch(() => null);
      if (metrics) set({ metrics });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : "Failed to run simulation" });
    } finally {
      set({ loading: false });
    }
  },
}));
