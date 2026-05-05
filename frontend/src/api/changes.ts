import type { Commit, CommitDetail, CommitListResponse } from "../types/common";
import { get, post } from "./client";

export async function listChanges(projectId: number): Promise<CommitListResponse> {
  return get<CommitListResponse>(`/projects/${projectId}/changes`);
}

export async function getChange(projectId: number, commitId: number): Promise<CommitDetail> {
  return get<CommitDetail>(`/projects/${projectId}/changes/${commitId}`);
}

export async function scanCommit(projectId: number, commitHash: string): Promise<Commit> {
  return post<Commit>(`/projects/${projectId}/changes/scan`, { commit_hash: commitHash });
}

export async function scanRecent(projectId: number, count: number): Promise<CommitListResponse> {
  return post<CommitListResponse>(`/projects/${projectId}/changes/scan-recent`, { count });
}
