import type { DocImpact, DocImpactListResponse } from "../types/common";
import { get, post, put } from "./client";

export async function listImpacts(projectId: number): Promise<DocImpactListResponse> {
  return get<DocImpactListResponse>(`/projects/${projectId}/impacts`);
}

export async function analyzeCommit(projectId: number, commitId: number): Promise<DocImpactListResponse> {
  return post<DocImpactListResponse>(`/projects/${projectId}/changes/${commitId}/analyze`);
}

export async function updateImpactStatus(
  projectId: number,
  impactId: number,
  status: string,
): Promise<DocImpact> {
  return put<DocImpact>(`/projects/${projectId}/impacts/${impactId}/status`, { status });
}
