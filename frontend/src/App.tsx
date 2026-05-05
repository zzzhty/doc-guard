import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ChangeDetail from "./pages/Changes/ChangeDetail";
import Dashboard from "./pages/Dashboard";
import DocPRList from "./pages/DocPRs/DocPRList";
import PatchPreview from "./pages/Patches/PatchPreview";
import ProjectConnect from "./pages/Projects/ProjectConnect";
import ProjectDetail from "./pages/Projects/ProjectDetail";
import ProjectList from "./pages/Projects/ProjectList";

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/projects" element={<ProjectList />} />
        <Route path="/projects/connect" element={<ProjectConnect />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
        <Route path="/projects/:id/doc-prs" element={<DocPRList />} />
        <Route path="/projects/:id/changes/:commitId" element={<ChangeDetail />} />
        <Route path="/projects/:id/patches/:patchId" element={<PatchPreview />} />
      </Route>
    </Routes>
  );
}

export default App;
