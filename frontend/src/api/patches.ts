import type { Patch } from "../types/common";
import { get, post, put } from "./client";

export async function generatePatch(
  projectId: number,
  impactId: number,
  changeType = "update_section",
): Promise<Patch> {
  return post<Patch>(`/projects/${projectId}/impacts/${impactId}/patches?change_type=${changeType}`);
}

export async function getPatch(patchId: number): Promise<Patch> {
  return get<Patch>(`/projects/patches/${patchId}`);
}

export async function updatePatch(patchId: number, patchedContent: string): Promise<Patch> {
  return put<Patch>(`/projects/patches/${patchId}`, { patched_content: patchedContent });
}

export async function approvePatch(patchId: number): Promise<Patch> {
  return post<Patch>(`/projects/patches/${patchId}/approve`);
}

export async function rejectPatch(patchId: number): Promise<Patch> {
  return post<Patch>(`/projects/patches/${patchId}/reject`);
}
