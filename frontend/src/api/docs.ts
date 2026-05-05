import type { DocContent, DocTreeResponse } from "../types/common";
import { get } from "./client";

export async function getDocTree(projectId: number): Promise<DocTreeResponse> {
  return get<DocTreeResponse>(`/projects/${projectId}/docs/tree`);
}

export async function getDocContent(projectId: number, path: string): Promise<DocContent> {
  return get<DocContent>(`/projects/${projectId}/docs/content?path=${encodeURIComponent(path)}`);
}
