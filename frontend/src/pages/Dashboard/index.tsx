import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useDashboard } from "../../hooks/useDashboard";
import { useProjects } from "../../hooks/useProjects";

export default function Dashboard() {
  const { data: projectData, isLoading: isProjectsLoading } = useProjects();
  const projects = useMemo(() => projectData?.projects || [], [projectData?.projects]);
  const [selectedProjectOverride, setSelectedProjectOverride] = useState<number | null>(null);

  const selectedProjectId = projects.some((project) => project.id === selectedProjectOverride)
    ? selectedProjectOverride
    : projects[0]?.id ?? null;
  const selectedProject = projects.find((project) => project.id === selectedProjectId);
  const { data: dashboard, isLoading: isDashboardLoading } = useDashboard(selectedProjectId);
  const stats = dashboard?.stats;

  if (isProjectsLoading) {
    return <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />;
  }

  if (projects.length === 0) {
    return (
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
          <p className="text-gray-600 mb-4">No projects connected.</p>
          <Link to="/projects/connect" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Connect Project
          </Link>
        </div>
      </div>
    );
  }

  const statCards = [
    { label: "Commits Scanned", value: stats?.commits_scanned ?? 0, className: "text-slate-700" },
    { label: "Pending Analysis", value: stats?.pending_analysis ?? 0, className: "text-amber-700" },
    { label: "Patch Generated", value: stats?.patch_generated ?? 0, className: "text-blue-700" },
    { label: "Open PRs", value: stats?.prs_open ?? 0, className: "text-sky-700" },
    { label: "Merged PRs", value: stats?.prs_merged ?? 0, className: "text-green-700" },
    { label: "Rejected PRs", value: stats?.prs_rejected ?? 0, className: "text-red-700" },
  ];

  return (
    <div>
      <div className="flex items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">{selectedProject?.name}</p>
        </div>
        <select
          value={selectedProjectId ?? ""}
          onChange={(event) => setSelectedProjectOverride(Number(event.target.value))}
          className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700"
        >
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      {isDashboardLoading ? (
        <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
            {statCards.map((stat) => (
              <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-5">
                <p className="text-xs text-gray-500 uppercase">{stat.label}</p>
                <p className={`text-3xl font-bold mt-2 ${stat.className}`}>{stat.value}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2 bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
                {selectedProjectId && (
                  <Link
                    to={`/projects/${selectedProjectId}/doc-prs`}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    Doc PRs
                  </Link>
                )}
              </div>
              <div className="divide-y divide-gray-100">
                {dashboard?.recent_activity.length ? (
                  dashboard.recent_activity.map((activity) => (
                    <div key={activity.id} className="px-6 py-4">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="font-mono text-sm text-gray-900">{activity.document_path}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(activity.created_at).toLocaleString()}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-1 rounded-md ${impactBadgeClass(activity.impact_level)}`}>
                            {activity.impact_level}
                          </span>
                          <span className="text-xs px-2 py-1 rounded-md bg-gray-100 text-gray-600">
                            {activity.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="px-6 py-8 text-sm text-gray-500">No recent activity.</p>
                )}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Project Actions</h2>
              <div className="space-y-3">
                {selectedProjectId && (
                  <>
                    <Link
                      to={`/projects/${selectedProjectId}`}
                      className="block p-4 bg-gray-50 rounded-lg hover:bg-blue-50 transition-colors"
                    >
                      <p className="font-medium text-gray-900">Project Detail</p>
                      <p className="text-sm text-gray-500 mt-1">Docs, commits, and impact analysis</p>
                    </Link>
                    <Link
                      to={`/projects/${selectedProjectId}/doc-prs`}
                      className="block p-4 bg-gray-50 rounded-lg hover:bg-blue-50 transition-colors"
                    >
                      <p className="font-medium text-gray-900">Doc PRs</p>
                      <p className="text-sm text-gray-500 mt-1">Refresh status and open remote PRs</p>
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function impactBadgeClass(level: string) {
  if (level === "high") return "bg-red-100 text-red-700";
  if (level === "medium") return "bg-amber-100 text-amber-700";
  if (level === "low") return "bg-green-100 text-green-700";
  return "bg-gray-100 text-gray-600";
}
