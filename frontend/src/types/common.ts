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

export interface DocOpsModulePreview {
  name: string;
  owner: string;
  code_paths: string[];
  docs: string[];
}

export interface DocOpsPreviewResponse {
  project_id: number;
  yaml: string;
  modules: DocOpsModulePreview[];
  docs_root: string;
  wiki_root: string;
  meta_root: string;
  warnings: string[];
  persisted: boolean;
}

export interface Commit {
  id: number;
  project_id: number;
  commit_hash: string;
  author: string;
  message: string;
  changed_files: string[];
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

export type DocTree = {
  [path: string]: DocTree | null;
};

export interface DocTreeResponse {
  docs: DocTree;
  wiki: DocTree;
}

export interface DocContent {
  path: string;
  content: string;
}

export interface DocImpact {
  id: number;
  commit_id: number;
  document_path: string;
  module_name: string;
  impact_level: "high" | "medium" | "low" | string;
  reason: string | null;
  confidence: number;
  patch_id: number | null;
  doc_pr_id: number | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DocImpactListResponse {
  impacts: DocImpact[];
  total: number;
}

export interface Patch {
  id: number;
  doc_impact_id: number;
  document_path: string;
  change_type: string;
  original_content: string | null;
  patched_content: string | null;
  diff: string | null;
  quality_report: string | null;
  status: string;
}

export interface DocPR {
  id: number;
  project_id: number;
  branch_name: string;
  base_branch: string;
  pr_number: number | null;
  pr_url: string | null;
  title: string | null;
  body: string | null;
  status: string;
  source_commit: string | null;
  created_at: string;
  merged_at: string | null;
}

export interface DocPRListResponse {
  prs: DocPR[];
  total: number;
}

export interface DashboardStats {
  pending_analysis: number;
  patch_generated: number;
  pr_created: number;
  pr_merged: number;
  pr_rejected: number;
  ignored: number;
  false_positive: number;
  high_risk: number;
  commits_scanned: number;
  total_doc_prs: number;
  prs_open: number;
  prs_merged: number;
  prs_rejected: number;
}

export interface DashboardActivity {
  id: number;
  document_path: string;
  impact_level: string;
  status: string;
  created_at: string;
}

export interface DashboardResponse {
  stats: DashboardStats;
  recent_activity: DashboardActivity[];
}
