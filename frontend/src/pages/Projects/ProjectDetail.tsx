import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import ChangeList from "../Changes/ChangeList";
import { useDocContent, useDocTree } from "../../hooks/useDocs";
import { usePreviewDocOps, useProject, useSaveDocOpsConfig, useSyncProject } from "../../hooks/useProjects";
import type { DocTree } from "../../types/common";

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const { data: project, isLoading, error } = useProject(projectId);
  const { data: docTree, isLoading: isDocsLoading } = useDocTree(projectId);
  const syncMutation = useSyncProject();
  const previewDocOpsMutation = usePreviewDocOps();
  const saveDocOpsMutation = useSaveDocOpsConfig();
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const [docOpsDraft, setDocOpsDraft] = useState("");
  const [docOpsMessage, setDocOpsMessage] = useState("");
  const { data: docContent, isLoading: isDocLoading } = useDocContent(projectId, selectedDoc);

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-4" />
        <div className="h-4 bg-gray-100 rounded w-2/3 mb-8" />
        <div className="h-64 bg-gray-100 rounded" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-600 mb-3">Failed to load project</p>
        <Link to="/projects" className="text-blue-600 hover:underline">Back to projects</Link>
      </div>
    );
  }

  const displayedDocOps = docOpsDraft || project.config_yaml || "";

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <Link to="/projects" className="text-sm text-gray-500 hover:text-gray-700 mb-2 block">
            &larr; Projects
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
          <p className="text-gray-500 mt-1">{project.repo_url}</p>
        </div>
        <div className="flex gap-2">
          <Link
            to={`/projects/${projectId}/doc-prs`}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Doc PRs
          </Link>
          <button
            onClick={() => syncMutation.mutate(projectId)}
            disabled={syncMutation.isPending}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
          >
            {syncMutation.isPending ? "Syncing..." : "Sync"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          { label: "Provider", value: project.provider },
          { label: "Branch", value: project.default_branch },
          { label: "DocOps", value: project.config_yaml ? "Configured" : "Missing" },
          { label: "Last Synced", value: project.last_synced_at ? new Date(project.last_synced_at).toLocaleDateString() : "Never" },
        ].map((item) => (
          <div key={item.label} className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs text-gray-400 uppercase">{item.label}</p>
            <p className="font-medium text-gray-900 mt-1">{item.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">DocOps Config</h2>
            <p className="text-sm text-gray-500 mt-1">
              {project.config_yaml ? "Saved config is available for analysis." : "Generate a candidate config before analysis."}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => {
                setDocOpsMessage("");
                previewDocOpsMutation.mutate(projectId, {
                  onSuccess: (draft) => {
                    setDocOpsDraft(draft.yaml);
                    setDocOpsMessage(`Generated ${draft.modules.length} module mapping(s).`);
                  },
                  onError: (err) => setDocOpsMessage(err instanceof Error ? err.message : "Failed to generate config."),
                });
              }}
              disabled={previewDocOpsMutation.isPending}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
            >
              {previewDocOpsMutation.isPending ? "Generating..." : "Generate Draft"}
            </button>
            <button
              type="button"
              onClick={() => {
                setDocOpsMessage("");
                saveDocOpsMutation.mutate(
                  { id: projectId, configYaml: displayedDocOps },
                  {
                    onSuccess: () => {
                      setDocOpsDraft("");
                      setDocOpsMessage("DocOps config saved.");
                    },
                    onError: (err) => setDocOpsMessage(err instanceof Error ? err.message : "Failed to save config."),
                  },
                );
              }}
              disabled={!displayedDocOps.trim() || saveDocOpsMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {saveDocOpsMutation.isPending ? "Saving..." : "Save Config"}
            </button>
          </div>
        </div>
        <textarea
          value={displayedDocOps}
          onChange={(event) => setDocOpsDraft(event.target.value)}
          placeholder="No DocOps config saved yet."
          className="w-full min-h-64 bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto text-sm font-mono whitespace-pre"
        />
        {previewDocOpsMutation.data?.warnings.length ? (
          <div className="mt-3 text-sm text-amber-700">
            {previewDocOpsMutation.data.warnings.map((warning) => (
              <p key={warning}>{warning}</p>
            ))}
          </div>
        ) : null}
        {docOpsMessage && <p className="text-sm text-gray-500 mt-3">{docOpsMessage}</p>}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Documentation</h2>
          {isDocsLoading && <p className="text-sm text-gray-500">Loading documentation tree...</p>}
          {docTree && (
            <div className="space-y-5">
              <DocTreeSection title="docs" tree={docTree.docs} onSelect={setSelectedDoc} selected={selectedDoc} />
              <DocTreeSection title="wiki" tree={docTree.wiki} onSelect={setSelectedDoc} selected={selectedDoc} />
              {Object.keys(docTree.docs).length === 0 && Object.keys(docTree.wiki).length === 0 && (
                <p className="text-sm text-gray-500">No docs or wiki files found.</p>
              )}
            </div>
          )}
        </div>

        <div className="xl:col-span-2 bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Document Content</h2>
            <p className="text-sm text-gray-500 mt-1">{selectedDoc || "Select a document to preview it."}</p>
          </div>
          <div className="p-6">
            {isDocLoading && <p className="text-sm text-gray-500">Loading document...</p>}
            {!selectedDoc && <p className="text-sm text-gray-500">No document selected.</p>}
            {docContent && (
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto text-sm font-mono max-h-[520px] whitespace-pre-wrap">
                {docContent.content}
              </pre>
            )}
          </div>
        </div>
      </div>

      <ChangeList projectId={projectId} />
    </div>
  );
}

interface DocTreeSectionProps {
  title: string;
  tree: DocTree;
  selected: string | null;
  onSelect: (path: string) => void;
}

function DocTreeSection({ title, tree, selected, onSelect }: DocTreeSectionProps) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">{title}</h3>
      {Object.keys(tree).length === 0 ? (
        <p className="text-sm text-gray-500">No {title} files found.</p>
      ) : (
        <DocTreeNode tree={tree} selected={selected} onSelect={onSelect} />
      )}
    </div>
  );
}

function DocTreeNode({ tree, selected, onSelect }: Omit<DocTreeSectionProps, "title">) {
  return (
    <ul className="space-y-1">
      {Object.entries(tree).map(([path, child]) => (
        <li key={path}>
          {child === null ? (
            <button
              type="button"
              onClick={() => onSelect(path)}
              className={`w-full text-left text-sm font-mono px-2 py-1 rounded ${
                selected === path ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-50"
              }`}
            >
              {path}
            </button>
          ) : (
            <div>
              <p className="text-xs font-medium text-gray-500 mt-2 mb-1">{path}</p>
              <div className="pl-3 border-l border-gray-100">
                <DocTreeNode tree={child} selected={selected} onSelect={onSelect} />
              </div>
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
