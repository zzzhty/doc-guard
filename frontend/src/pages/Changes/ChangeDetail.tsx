import { Link, useNavigate, useParams } from "react-router-dom";
import { useChange } from "../../hooks/useChanges";
import { useAnalyzeCommit, useImpacts, useUpdateImpactStatus } from "../../hooks/useImpacts";
import { useGeneratePatch } from "../../hooks/usePatches";

export default function ChangeDetail() {
  const { id, commitId } = useParams<{ id: string; commitId: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);
  const { data: commit, isLoading, error } = useChange(projectId, Number(commitId));
  const analyzeMutation = useAnalyzeCommit(projectId, Number(commitId));
  const updateImpactStatus = useUpdateImpactStatus(projectId);
  const generatePatch = useGeneratePatch(projectId);
  const { data: impactData, isLoading: isImpactsLoading } = useImpacts(projectId);

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-6 bg-gray-200 rounded w-1/4" />
        <div className="h-4 bg-gray-100 rounded w-1/2" />
        <div className="h-96 bg-gray-100 rounded" />
      </div>
    );
  }

  if (error || !commit) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-600">Failed to load commit diff</p>
      </div>
    );
  }

  const impacts = (impactData?.impacts || []).filter((impact) => impact.commit_id === commit.id);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Link to={`/projects/${projectId}`} className="text-sm text-gray-500 hover:text-gray-700">
          &larr; Project
        </Link>
        <button
          type="button"
          onClick={() => analyzeMutation.mutate()}
          disabled={analyzeMutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
        >
          {analyzeMutation.isPending ? "Analyzing..." : "Analyze Impact"}
        </button>
      </div>
      {analyzeMutation.isError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {analyzeMutation.error instanceof Error ? analyzeMutation.error.message : "Impact analysis failed"}
        </div>
      )}
      {generatePatch.isError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {generatePatch.error instanceof Error ? generatePatch.error.message : "Patch generation failed"}
        </div>
      )}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-lg font-semibold text-gray-900 font-mono">
            {commit.commit_hash}
          </h1>
          <p className="text-sm text-gray-500 mt-1">{commit.author}</p>
          <p className="text-sm text-gray-700 mt-2 whitespace-pre-wrap">{commit.message}</p>
          <div className="mt-4">
            <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Changed Files</h2>
            {commit.changed_files.length > 0 ? (
              <ul className="space-y-1">
                {commit.changed_files.map((file) => (
                  <li key={file} className="font-mono text-sm text-gray-700 bg-gray-50 px-2 py-1 rounded">
                    {file}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">No changed files recorded.</p>
            )}
          </div>
        </div>

        <div className="p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-3">Diff</h2>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto text-sm font-mono max-h-[600px] whitespace-pre-wrap">
            {commit.diff || "No diff available"}
          </pre>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mt-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Documentation Impact</h2>
        </div>
        <div className="p-6">
          {isImpactsLoading && <p className="text-sm text-gray-500">Loading impacts...</p>}
          {!isImpactsLoading && impacts.length === 0 && (
            <p className="text-sm text-gray-500">
              No affected docs found yet. Run impact analysis for this commit.
            </p>
          )}
          {impacts.length > 0 && (
            <div className="space-y-3">
              {impacts.map((impact) => (
                <div key={impact.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-mono text-sm text-gray-900">{impact.document_path}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        {impact.module_name} · confidence {Math.round(impact.confidence * 100)}%
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded-md ${impactBadgeClass(impact.impact_level)}`}>
                        {impact.impact_level}
                      </span>
                      <span className="text-xs px-2 py-1 rounded-md bg-gray-100 text-gray-600">
                        {impact.status}
                      </span>
                    </div>
                  </div>
                  {impact.reason && <p className="text-sm text-gray-700 mt-3">{impact.reason}</p>}
                  <div className="flex gap-2 mt-4">
                    {impact.patch_id ? (
                      <Link
                        to={`/projects/${projectId}/patches/${impact.patch_id}`}
                        className="px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                      >
                        View Patch
                      </Link>
                    ) : (
                      <button
                        type="button"
                        disabled={generatePatch.isPending}
                        onClick={() =>
                          generatePatch.mutate(
                            { impactId: impact.id },
                            {
                              onSuccess: (patch) => navigate(`/projects/${projectId}/patches/${patch.id}`),
                            },
                          )
                        }
                        className="px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm"
                      >
                        {generatePatch.isPending ? "Generating..." : "Generate Patch"}
                      </button>
                    )}
                    <button
                      type="button"
                      disabled={updateImpactStatus.isPending}
                      onClick={() => updateImpactStatus.mutate({ impactId: impact.id, status: "ignored" })}
                      className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 text-sm"
                    >
                      Ignore
                    </button>
                    <button
                      type="button"
                      disabled={updateImpactStatus.isPending}
                      onClick={() => updateImpactStatus.mutate({ impactId: impact.id, status: "false_positive" })}
                      className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 text-sm"
                    >
                      False Positive
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function impactBadgeClass(level: string) {
  if (level === "high") return "bg-red-100 text-red-700";
  if (level === "medium") return "bg-amber-100 text-amber-700";
  if (level === "low") return "bg-green-100 text-green-700";
  return "bg-gray-100 text-gray-600";
}
