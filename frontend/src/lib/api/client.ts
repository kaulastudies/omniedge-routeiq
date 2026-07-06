import {
  MetricsResponse,
  RouteRequestParams,
  RouteResponse,
  Simulation,
  StatusResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class RouteIQApi {
  /**
   * Fetches the current system status and provider health.
   */
  static async getStatus(): Promise<StatusResponse> {
    const res = await fetch(`${API_BASE}/status`);
    if (!res.ok) throw new Error("Failed to fetch status");
    return res.json();
  }

  /**
   * Fetches dashboard usage metrics.
   */
  static async getMetrics(): Promise<MetricsResponse> {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) throw new Error("Failed to fetch metrics");
    return res.json();
  }

  /**
   * Fetches available simulation scenarios.
   */
  static async getSimulations(): Promise<{ scenarios: Simulation[] }> {
    const res = await fetch(`${API_BASE}/simulations`);
    if (!res.ok) throw new Error("Failed to fetch simulations");
    return res.json();
  }

  /**
   * Submits a routing task.
   */
  static async runRoute(params: RouteRequestParams): Promise<RouteResponse> {
    const res = await fetch(`${API_BASE}/route`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error("Route request failed");
    return res.json();
  }

  /**
   * Executes a registered simulation.
   */
  static async runSimulation(id: string): Promise<RouteResponse> {
    const res = await fetch(`${API_BASE}/simulations/${id}`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Simulation request failed");
    return res.json();
  }
}
