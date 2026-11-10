import type { DashboardData, SaveStrategyResponse, Strategy } from "./types";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function fetchDashboard(): Promise<DashboardData> {
  return getJson<DashboardData>("/api/dashboard");
}

export async function saveStrategy(strategy: Strategy): Promise<SaveStrategyResponse> {
  const response = await fetch("/api/strategy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: strategy.name,
      policyText: strategy.policyText,
      risk: strategy.risk,
      advanced: strategy.advanced
    })
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<SaveStrategyResponse>;
}
