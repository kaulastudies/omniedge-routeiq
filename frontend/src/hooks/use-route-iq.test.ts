/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useRouteIQ } from "./use-route-iq";
import { RouteIQApi } from "../lib/api/client";

vi.mock("../lib/api/client", () => ({
  RouteIQApi: {
    getStatus: vi.fn(),
    getMetrics: vi.fn(),
    getSimulations: vi.fn(),
    runRoute: vi.fn(),
    runSimulation: vi.fn(),
  },
}));

describe("useRouteIQ Hook", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    useRouteIQ.setState({
      status: null,
      metrics: null,
      simulations: [],
      routeResult: null,
      loading: false,
      error: null,
    });
  });

  describe("refreshData", () => {
    it("should update state successfully when API calls resolve", async () => {
      const mockStatus = { status: "ok", providers: [] } as any;
      const mockMetrics = { total_requests: 10 } as any;
      const mockSimulations = { scenarios: [{ id: "sim-1" }] } as any;

      (RouteIQApi.getStatus as any).mockResolvedValue(mockStatus);
      (RouteIQApi.getMetrics as any).mockResolvedValue(mockMetrics);
      (RouteIQApi.getSimulations as any).mockResolvedValue(mockSimulations);

      await useRouteIQ.getState().refreshData();

      const state = useRouteIQ.getState();
      expect(state.status).toEqual(mockStatus);
      expect(state.metrics).toEqual(mockMetrics);
      expect(state.simulations).toEqual([{ id: "sim-1" }]);
      expect(state.error).toBeNull();
    });

    it("should retain old state on partial failure and not crash", async () => {
      const mockStatus = { status: "ok" } as any;
      (RouteIQApi.getStatus as any).mockResolvedValue(mockStatus);
      (RouteIQApi.getMetrics as any).mockRejectedValue(new Error("Network Error"));
      (RouteIQApi.getSimulations as any).mockRejectedValue(new Error("Network Error"));

      await useRouteIQ.getState().refreshData();

      const state = useRouteIQ.getState();
      expect(state.status).toEqual(mockStatus);
      expect(state.metrics).toBeNull(); // remains null since initial is null
      expect(state.simulations).toEqual([]);
    });
  });

  describe("runRoute", () => {
    it("should set loading to true, call API, update routeResult, and auto-refresh metrics", async () => {
      const mockResult = { request_id: "test" } as any;
      const mockMetrics = { total_requests: 15 } as any;

      (RouteIQApi.runRoute as any).mockResolvedValue(mockResult);
      (RouteIQApi.getMetrics as any).mockResolvedValue(mockMetrics);

      const promise = useRouteIQ
        .getState()
        .runRoute({ prompt: "test", task_type: "t", privacy_level: "p" });

      expect(useRouteIQ.getState().loading).toBe(true);
      await promise;

      const state = useRouteIQ.getState();
      expect(state.loading).toBe(false);
      expect(state.routeResult).toEqual(mockResult);
      expect(state.metrics).toEqual(mockMetrics);
    });

    it("should properly catch errors and set loading to false", async () => {
      (RouteIQApi.runRoute as any).mockRejectedValue(new Error("Failed to route"));

      await useRouteIQ.getState().runRoute({ prompt: "", task_type: "", privacy_level: "" });

      const state = useRouteIQ.getState();
      expect(state.loading).toBe(false);
      expect(state.error).toBe("Failed to route");
    });
  });
});
