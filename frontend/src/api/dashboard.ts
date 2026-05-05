import type { DashboardResponse } from "../types/common";
import { get } from "./client";

export async function getDashboard(projectId: number): Promise<DashboardResponse> {
  return get<DashboardResponse>(`/dashboard/projects/${projectId}`);
}
