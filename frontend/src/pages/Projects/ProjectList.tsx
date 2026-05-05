import { Link } from "react-router-dom";
import { useDeleteProject, useProjects } from "../../hooks/useProjects";

export default function ProjectList() {
  const { data, isLoading, error } = useProjects();
  const deleteMutation = useDeleteProject();

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
        <Link
          to="/projects/connect"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Connect Project
        </Link>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
              <div className="h-5 bg-gray-200 rounded w-3/4 mb-3" />
              <div className="h-4 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-600 mb-3">Failed to load projects</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      {data && data.projects.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <p className="text-gray-500 text-lg mb-4">No projects connected yet</p>
          <Link
            to="/projects/connect"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Connect your first project
          </Link>
        </div>
      )}

      {data && data.projects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.projects.map((project) => (
            <div
              key={project.id}
              className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <Link to={`/projects/${project.id}`} className="flex-1">
                  <h3 className="font-semibold text-gray-900 hover:text-blue-600">{project.name}</h3>
                  <p className="text-sm text-gray-500 mt-1 truncate">{project.repo_url}</p>
                  <div className="flex gap-3 mt-3">
                    <span className="text-xs px-2 py-1 bg-gray-100 rounded-md text-gray-600">
                      {project.provider}
                    </span>
                    <span className="text-xs px-2 py-1 bg-gray-100 rounded-md text-gray-600">
                      {project.default_branch}
                    </span>
                  </div>
                </Link>
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    if (confirm("Delete this project?")) {
                      deleteMutation.mutate(project.id);
                    }
                  }}
                  className="text-sm text-red-500 hover:text-red-700 ml-4"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
