import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider } from "./lib/store";
import { Layout } from "./components/Layout";

const Dashboard = lazy(() => import("./pages/Dashboard").then((module) => ({ default: module.Dashboard })));
const LogsExplorer = lazy(() => import("./pages/LogsExplorer").then((module) => ({ default: module.LogsExplorer })));
const Incidents = lazy(() => import("./pages/Incidents").then((module) => ({ default: module.Incidents })));
const IncidentDetail = lazy(() => import("./pages/IncidentDetail").then((module) => ({ default: module.IncidentDetail })));
const Services = lazy(() => import("./pages/Services").then((module) => ({ default: module.Services })));

function RoutesWithLayout() {
  return (
    <Layout>
      <Suspense fallback={<div className="grid h-64 place-items-center text-sm text-muted-foreground">Loading view…</div>}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/logs" element={<LogsExplorer />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/incidents/:id" element={<IncidentDetail />} />
          <Route path="/services" element={<Services />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
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
