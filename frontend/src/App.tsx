import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
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
      </Route>
    </Routes>
  );
}

export default App;
