import type { DocPR, DocPRListResponse } from "../types/common";
import { get, post } from "./client";

export async function createDocPR(projectId: number, patchIds: number[]): Promise<DocPR> {
  return post<DocPR>(`/projects/${projectId}/doc-prs`, { patch_ids: patchIds });
}

export async function listDocPRs(projectId: number): Promise<DocPRListResponse> {
  return get<DocPRListResponse>(`/projects/${projectId}/doc-prs`);
}

export async function getDocPR(docPrId: number): Promise<DocPR> {
  return get<DocPR>(`/projects/doc-prs/${docPrId}`);
}

export async function refreshDocPR(docPrId: number): Promise<DocPR> {
  return post<DocPR>(`/projects/doc-prs/${docPrId}/refresh`);
}

export async function closeDocPR(docPrId: number): Promise<DocPR> {
  return post<DocPR>(`/projects/doc-prs/${docPrId}/close`);
}
