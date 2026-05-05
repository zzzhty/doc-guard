import type { Project, ProjectCreate, ProjectListResponse } from "../types/common";
import { del, get, post, put } from "./client";

export async function listProjects(): Promise<ProjectListResponse> {
  return get<ProjectListResponse>("/projects");
}

export async function getProject(id: number): Promise<Project> {
  return get<Project>(`/projects/${id}`);
}

export async function createProject(data: ProjectCreate): Promise<Project> {
  return post<Project>("/projects", data);
}

export async function updateProject(id: number, data: Partial<ProjectCreate>): Promise<Project> {
  return put<Project>(`/projects/${id}`, data);
}

export async function deleteProject(id: number): Promise<void> {
  return del(`/projects/${id}`);
}

export async function syncProject(id: number): Promise<Project> {
  return post<Project>(`/projects/${id}/sync`);
}
