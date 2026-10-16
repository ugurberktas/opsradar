import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { apiService, DashboardStats, Incident, Service, LogEvent } from "./api";

interface AppState {
  services: Service[];
  incidents: Incident[];
  logs: LogEvent[];
  dashboard: DashboardStats | null;
  loading: Record<string, boolean>;
  theme: "dark" | "light";
  setTheme: (t: "dark" | "light") => void;
  refresh: () => Promise<void>;
  acknowledgeIncident: (id: number) => Promise<void>;
  resolveIncident: (id: number) => Promise<void>;
  simulate: (seed?: number, total_events?: number) => Promise<any>;
  ingestLogs: (events: any[]) => Promise<any>;
}

const AppContext = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [services, setServices] = useState<Service[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [dashboard, setDashboard] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [theme, setThemeState] = useState<"dark" | "light">("dark");

  const setLoadingState = useCallback((key: string, v: boolean) => {
    setLoading((prev) => ({ ...prev, [key]: v }));
  }, []);

  const setTheme = useCallback((t: "dark" | "light") => {
    setThemeState(t);
    if (t === "dark") document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
    localStorage.setItem("opsradar-theme", t);
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem("opsradar-theme") as "dark" | "light" | null;
    setTheme(saved || "dark");
  }, [setTheme]);

  const fetchServices = useCallback(async () => {
    setLoadingState("services", true);
    try {
      const r = await apiService.services();
      setServices(r.data);
    } finally {
      setLoadingState("services", false);
    }
  }, [setLoadingState]);

  const fetchDashboard = useCallback(async () => {
    setLoadingState("dashboard", true);
    try {
      const r = await apiService.dashboard();
      setDashboard(r.data);
    } finally {
      setLoadingState("dashboard", false);
    }
  }, [setLoadingState]);

  const fetchIncidents = useCallback(async () => {
    setLoadingState("incidents", true);
    try {
      const r = await apiService.incidents();
      setIncidents(r.data);
    } finally {
      setLoadingState("incidents", false);
    }
  }, [setLoadingState]);

  const fetchLogs = useCallback(async () => {
    setLoadingState("logs", true);
    try {
      const r = await apiService.logs({ limit: 100 });
      setLogs(r.data);
    } finally {
      setLoadingState("logs", false);
    }
  }, [setLoadingState]);

  const refresh = useCallback(async () => {
    await Promise.all([fetchServices(), fetchDashboard(), fetchIncidents(), fetchLogs()]);
  }, [fetchServices, fetchDashboard, fetchIncidents, fetchLogs]);

  const acknowledgeIncident = useCallback(async (id: number) => {
    const r = await apiService.updateIncident(id, "acknowledged");
    setIncidents((prev) => {
      const idx = prev.findIndex((x) => x.id === id);
      if (idx < 0) return prev;
      const next = [...prev];
      next[idx] = r.data;
      return next;
    });
  }, []);

  const resolveIncident = useCallback(async (id: number) => {
    const r = await apiService.updateIncident(id, "resolved");
    setIncidents((prev) => {
      const idx = prev.findIndex((x) => x.id === id);
      if (idx < 0) return prev;
      const next = [...prev];
      next[idx] = r.data;
      return next;
    });
  }, []);

  const simulate = useCallback(async (seed?: number, total_events?: number) => {
    setLoadingState("simulate", true);
    try {
      const r = await apiService.simulate(seed, total_events);
      await refresh();
      return r.data;
    } finally {
      setLoadingState("simulate", false);
    }
  }, [setLoadingState, refresh]);

  const ingestLogs = useCallback(async (events: any[]) => {
    setLoadingState("ingest", true);
    try {
      const r = await apiService.ingestLogs(events);
      await refresh();
      return r.data;
    } finally {
      setLoadingState("ingest", false);
    }
  }, [setLoadingState, refresh]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <AppContext.Provider
      value={{
        services,
        incidents,
        logs,
        dashboard,
        loading,
        theme,
        setTheme,
        refresh,
        acknowledgeIncident,
        resolveIncident,
        simulate,
        ingestLogs,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
