import { useMemo, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useParams } from "react-router-dom";
import { useCreateDocPR } from "../../hooks/useDocPrs";
import { useApprovePatch, usePatch, useRejectPatch, useUpdatePatch } from "../../hooks/usePatches";

export default function PatchPreview() {
  const { id, patchId } = useParams<{ id: string; patchId: string }>();
  const projectId = Number(id);
  const parsedPatchId = Number(patchId);
  const { data: patch, isLoading, error } = usePatch(parsedPatchId);
  const updateMutation = useUpdatePatch(parsedPatchId);
  const approveMutation = useApprovePatch(parsedPatchId);
  const rejectMutation = useRejectPatch(parsedPatchId);
  const createPrMutation = useCreateDocPR(projectId);
  const contentRef = useRef<HTMLTextAreaElement>(null);

  const quality = useMemo(() => parseQualityReport(patch?.quality_report), [patch?.quality_report]);

  if (isLoading) {
    return <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />;
  }

  if (error || !patch) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-600">Failed to load patch</p>
        <Link to={`/projects/${projectId}`} className="text-blue-600 hover:underline">
          Back to project
        </Link>
      </div>
    );
  }

  return (
    <div>
      <Link to={`/projects/${projectId}`} className="text-sm text-gray-500 hover:text-gray-700 mb-4 block">
        &larr; Project
      </Link>
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Patch Preview</h1>
          <p className="text-gray-500 mt-1 font-mono">{patch.document_path}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => updateMutation.mutate(contentRef.current?.value || patch.patched_content || "")}
            disabled={updateMutation.isPending || patch.status === "approved"}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 text-sm"
          >
            {updateMutation.isPending ? "Saving..." : "Save Edits"}
          </button>
          <button
            type="button"
            onClick={() => approveMutation.mutate()}
            disabled={approveMutation.isPending || patch.status === "approved"}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm"
          >
            {approveMutation.isPending ? "Approving..." : "Approve"}
          </button>
          <button
            type="button"
            onClick={() => rejectMutation.mutate()}
            disabled={rejectMutation.isPending || patch.status === "rejected"}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 text-sm"
          >
            {rejectMutation.isPending ? "Rejecting..." : "Reject"}
          </button>
          <button
            type="button"
            onClick={() => createPrMutation.mutate([patch.id])}
            disabled={createPrMutation.isPending || patch.status !== "approved"}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            {createPrMutation.isPending ? "Creating PR..." : "Create PR"}
          </button>
        </div>
      </div>
      {createPrMutation.isError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {createPrMutation.error instanceof Error ? createPrMutation.error.message : "PR creation failed"}
        </div>
      )}
      {createPrMutation.data && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-medium text-blue-900">{createPrMutation.data.title}</p>
              <p className="text-sm text-blue-700 mt-1">
                {createPrMutation.data.branch_name} · {createPrMutation.data.status}
              </p>
            </div>
            {createPrMutation.data.pr_url && (
              <a
                href={createPrMutation.data.pr_url}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
              >
                Open PR
              </a>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <DocumentPanel title="Original" content={patch.original_content || ""} />
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">Patched Content</h2>
          </div>
          <textarea
            key={patch.id}
            ref={contentRef}
            defaultValue={patch.patched_content || ""}
            className="w-full h-[460px] p-4 font-mono text-sm border-0 focus:outline-none focus:ring-0"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">Diff</h2>
          </div>
          <pre className="bg-gray-900 text-gray-100 p-4 overflow-auto text-sm font-mono max-h-[460px] whitespace-pre-wrap">
            {patch.diff || "No diff available"}
          </pre>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-3">Quality Report</h2>
          <div className="flex gap-2 mb-4">
            <span className="text-xs px-2 py-1 rounded-md bg-gray-100 text-gray-600">{patch.status}</span>
            <span className="text-xs px-2 py-1 rounded-md bg-gray-100 text-gray-600">
              score {quality?.overall_score ?? "n/a"}
            </span>
            {quality?.requires_review && (
              <span className="text-xs px-2 py-1 rounded-md bg-amber-100 text-amber-700">review required</span>
            )}
          </div>
          {quality?.issues.length ? (
            <ul className="space-y-2">
              {quality.issues.map((issue, index) => (
                <li key={`${issue.type}-${index}`} className="text-sm text-gray-700">
                  <span className="font-medium">{issue.severity}</span>: {issue.description}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">No quality issues reported.</p>
          )}
          <h2 className="font-semibold text-gray-900 mt-6 mb-3">Markdown Preview</h2>
          <div className="prose prose-sm max-w-none border border-gray-100 rounded-lg p-4 max-h-[260px] overflow-auto">
            <ReactMarkdown>{patch.patched_content || ""}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}

function DocumentPanel({ title, content }: { title: string; content: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="font-semibold text-gray-900">{title}</h2>
      </div>
      <pre className="bg-gray-900 text-gray-100 p-4 overflow-auto text-sm font-mono h-[460px] whitespace-pre-wrap">
        {content}
      </pre>
    </div>
  );
}

function parseQualityReport(report: string | null | undefined) {
  if (!report) return null;
  try {
    return JSON.parse(report) as {
      issues: Array<{ type: string; severity: string; description: string }>;
      overall_score: number;
      requires_review: boolean;
    };
  } catch {
    return null;
  }
}
