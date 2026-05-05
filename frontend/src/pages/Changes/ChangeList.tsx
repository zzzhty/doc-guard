import { useState } from "react";
import { useChanges, useScanCommit } from "../../hooks/useChanges";

interface Props {
  projectId: number;
}

export default function ChangeList({ projectId }: Props) {
  const { data, isLoading, error } = useChanges(projectId);
  const scanMutation = useScanCommit(projectId);
  const [commitHash, setCommitHash] = useState("");
  const [showScan, setShowScan] = useState(false);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commitHash.trim()) return;
    try {
      await scanMutation.mutateAsync(commitHash.trim());
      setCommitHash("");
      setShowScan(false);
    } catch {
      // error shown via mutation state
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Scanned Commits</h2>
        <button
          onClick={() => setShowScan(!showScan)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
        >
          Scan Commit
        </button>
      </div>

      {showScan && (
        <form onSubmit={handleScan} className="mb-4 flex gap-3">
          <input
            type="text"
            value={commitHash}
            onChange={(e) => setCommitHash(e.target.value)}
            placeholder="Enter commit hash..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={scanMutation.isPending}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm"
          >
            {scanMutation.isPending ? "Scanning..." : "Scan"}
          </button>
        </form>
      )}

      {scanMutation.isError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {scanMutation.error instanceof Error ? scanMutation.error.message : "Scan failed"}
        </div>
      )}

      {isLoading && (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          Failed to load commits. <button onClick={() => window.location.reload()} className="underline">Retry</button>
        </div>
      )}

      {data && data.commits.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No commits scanned yet. Scan a commit to begin.
        </div>
      )}

      {data && data.commits.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Hash</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Author</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Message</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.commits.map((commit) => (
                <tr key={commit.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-sm text-gray-900">
                    {commit.commit_hash.substring(0, 8)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{commit.author}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 max-w-xs truncate">
                    {commit.message}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded-md ${
                      commit.analysis_status === "completed"
                        ? "bg-green-100 text-green-700"
                        : commit.analysis_status === "analyzing"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-gray-100 text-gray-600"
                    }`}>
                      {commit.analysis_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
