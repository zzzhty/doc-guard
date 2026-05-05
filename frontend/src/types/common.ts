export interface Project {
  id: number;
  name: string;
  repo_url: string;
  provider: string;
  local_path: string | null;
  default_branch: string;
  config_yaml: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  repo_url: string;
  provider: string;
  auth_token?: string;
  default_branch?: string;
  local_path?: string;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
}

export interface Commit {
  id: number;
  project_id: number;
  commit_hash: string;
  author: string;
  message: string;
  committed_at: string | null;
  scanned_at: string | null;
  analysis_status: string;
}

export interface CommitDetail extends Commit {
  diff: string;
}

export interface CommitListResponse {
  commits: Commit[];
  total: number;
}
