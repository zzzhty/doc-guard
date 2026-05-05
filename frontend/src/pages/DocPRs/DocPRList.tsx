import { ExternalLink, RefreshCw, XCircle } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { useCloseDocPR, useDocPRs, useRefreshDocPR } from "../../hooks/useDocPrs";
import { useProject } from "../../hooks/useProjects";
import type { DocPR } from "../../types/common";

export default function DocPRList() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const { data: project } = useProject(projectId);
  const { data, isLoading, error } = useDocPRs(projectId);
  const refreshMutation = useRefreshDocPR(projectId);
  const closeMutation = useCloseDocPR(projectId);

  if (isLoading) {
    return <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-600">Failed to load Doc PRs</p>
      </div>
    );
  }

  const prs = data?.prs || [];

  return (
    <div>
      <Link to={`/projects/${projectId}`} className="text-sm text-gray-500 hover:text-gray-700 mb-4 block">
        &larr; Project
      </Link>
      <div className="flex items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Doc PRs</h1>
          <p className="text-gray-500 mt-1">{project?.name}</p>
        </div>
      </div>

      {(refreshMutation.isError || closeMutation.isError) && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {refreshMutation.error instanceof Error
            ? refreshMutation.error.message
            : closeMutation.error instanceof Error
              ? closeMutation.error.message
              : "Doc PR operation failed"}
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
        <div className="min-w-[920px]">
          <div className="grid grid-cols-[1.5fr_1fr_0.8fr_0.8fr_1fr] gap-4 px-6 py-3 bg-gray-50 text-xs uppercase text-gray-500">
            <span>Title</span>
            <span>Branch</span>
            <span>Source</span>
            <span>Status</span>
            <span className="text-right">Actions</span>
          </div>
          {prs.length === 0 ? (
            <p className="px-6 py-8 text-sm text-gray-500">No Doc PRs created yet.</p>
          ) : (
            <div className="divide-y divide-gray-100">
              {prs.map((pr) => (
                <DocPRRow
                  key={pr.id}
                  pr={pr}
                  onRefresh={() => refreshMutation.mutate(pr.id)}
                  onClose={() => closeMutation.mutate(pr.id)}
                  isBusy={refreshMutation.isPending || closeMutation.isPending}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DocPRRow({
  pr,
  onRefresh,
  onClose,
  isBusy,
}: {
  pr: DocPR;
  onRefresh: () => void;
  onClose: () => void;
  isBusy: boolean;
}) {
  const isClosed = pr.status === "merged" || pr.status === "closed" || pr.status === "rejected";

  return (
    <div className="grid grid-cols-[1.5fr_1fr_0.8fr_0.8fr_1fr] gap-4 px-6 py-4 items-center">
      <div>
        <p className="font-medium text-gray-900">{pr.title || "Untitled Doc PR"}</p>
        <p className="text-xs text-gray-500 mt-1">{new Date(pr.created_at).toLocaleString()}</p>
      </div>
      <p className="font-mono text-xs text-gray-700 truncate" title={pr.branch_name}>
        {pr.branch_name}
      </p>
      <p className="font-mono text-xs text-gray-700">{pr.source_commit?.slice(0, 7) || "unknown"}</p>
      <span className={`text-xs px-2 py-1 rounded-md w-fit ${statusBadgeClass(pr.status)}`}>
        {pr.status}
      </span>
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onRefresh}
          disabled={isBusy}
          className="p-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50"
          title="Refresh status"
          aria-label="Refresh status"
        >
          <RefreshCw size={16} />
        </button>
        <button
          type="button"
          onClick={onClose}
          disabled={isBusy || isClosed}
          className="p-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50"
          title="Close PR"
          aria-label="Close PR"
        >
          <XCircle size={16} />
        </button>
        {pr.pr_url && (
          <a
            href={pr.pr_url}
            target="_blank"
            rel="noreferrer"
            className="p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            title="Open remote PR"
            aria-label="Open remote PR"
          >
            <ExternalLink size={16} />
          </a>
        )}
      </div>
    </div>
  );
}

function statusBadgeClass(status: string) {
  if (status === "open") return "bg-blue-100 text-blue-700";
  if (status === "merged") return "bg-green-100 text-green-700";
  if (status === "closed" || status === "rejected") return "bg-red-100 text-red-700";
  if (status === "local_branch") return "bg-amber-100 text-amber-700";
  return "bg-gray-100 text-gray-600";
}
