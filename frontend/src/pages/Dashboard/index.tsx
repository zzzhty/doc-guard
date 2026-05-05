import { Link } from "react-router-dom";

export default function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {[
          { label: "Projects", value: "—", color: "blue" },
          { label: "Commits Scanned", value: "—", color: "green" },
          { label: "Doc Impacts", value: "—", color: "amber" },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-6">
            <p className="text-sm text-gray-500">{stat.label}</p>
            <p className={`text-3xl font-bold text-${stat.color}-600 mt-1`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Start</h2>
        <div className="space-y-3">
          <Link
            to="/projects"
            className="block p-4 bg-gray-50 rounded-lg hover:bg-blue-50 transition-colors"
          >
            <p className="font-medium text-gray-900">Connect a Project</p>
            <p className="text-sm text-gray-500 mt-1">
              Add a Git repository to start monitoring documentation health
            </p>
          </Link>
          <Link
            to="/projects"
            className="block p-4 bg-gray-50 rounded-lg hover:bg-blue-50 transition-colors"
          >
            <p className="font-medium text-gray-900">View Documentation</p>
            <p className="text-sm text-gray-500 mt-1">
              Browse project docs, wiki entries, and configuration
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
}
