import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider } from "./lib/store";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { LogsExplorer } from "./pages/LogsExplorer";
import { Incidents } from "./pages/Incidents";
import { IncidentDetail } from "./pages/IncidentDetail";
import { Services } from "./pages/Services";

function RoutesWithLayout() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/logs" element={<LogsExplorer />} />
        <Route path="/incidents" element={<Incidents />} />
        <Route path="/incidents/:id" element={<IncidentDetail />} />
        <Route path="/services" element={<Services />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <RoutesWithLayout />
      </BrowserRouter>
    </AppProvider>
  );
}
