import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateProject } from "../../hooks/useProjects";
import type { ProjectCreate } from "../../types/common";

export default function ProjectConnect() {
  const navigate = useNavigate();
  const mutation = useCreateProject();

  const [form, setForm] = useState<ProjectCreate>({
    name: "",
    repo_url: "",
    provider: "local",
    local_path: "",
    default_branch: "main",
  });
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const project = await mutation.mutateAsync(form);
      navigate(`/projects/${project.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to connect project");
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Connect Project</h1>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Project Name</label>
          <input
            type="text"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="my-project"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Provider</label>
          <select
            value={form.provider}
            onChange={(e) => setForm({ ...form, provider: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="local">Local Git</option>
            <option value="gitea">Gitea</option>
            <option value="gitlab">GitLab</option>
            <option value="github">GitHub</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Repository URL</label>
          <input
            type="text"
            value={form.repo_url}
            onChange={(e) => setForm({ ...form, repo_url: e.target.value })}
            placeholder={form.provider === "local" ? "/path/to/repo (or remote URL for clone)" : "https://..."}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {form.provider === "local" && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Local Path</label>
            <input
              type="text"
              required
              value={form.local_path || ""}
              onChange={(e) => setForm({ ...form, local_path: e.target.value })}
              placeholder="/absolute/path/to/repo"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        )}

        {form.provider !== "local" && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Personal Access Token</label>
            <input
              type="password"
              value={form.auth_token || ""}
              onChange={(e) => setForm({ ...form, auth_token: e.target.value })}
              placeholder="Access token for API authentication"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Default Branch</label>
          <input
            type="text"
            value={form.default_branch}
            onChange={(e) => setForm({ ...form, default_branch: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div className="flex gap-4 pt-2">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {mutation.isPending ? "Connecting..." : "Connect Project"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/projects")}
            className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
