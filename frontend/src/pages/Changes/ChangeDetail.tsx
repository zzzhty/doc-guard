import { useParams } from "react-router-dom";
import { useChange } from "../../hooks/useChanges";

interface Props {
  projectId: number;
}

export default function ChangeDetail({ projectId }: Props) {
  const { commitId } = useParams<{ commitId: string }>();
  const { data: commit, isLoading, error } = useChange(projectId, Number(commitId));

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

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 font-mono">
          {commit.commit_hash}
        </h3>
        <p className="text-sm text-gray-500 mt-1">{commit.author}</p>
        <p className="text-sm text-gray-700 mt-2 whitespace-pre-wrap">{commit.message}</p>
      </div>

      <div className="p-6">
        <h4 className="text-sm font-medium text-gray-500 uppercase mb-3">Diff</h4>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto text-sm font-mono max-h-[600px] whitespace-pre-wrap">
          {commit.diff || "No diff available"}
        </pre>
      </div>
    </div>
  );
}
