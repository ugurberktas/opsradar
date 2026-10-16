import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  apiService,
  DashboardStats,
  Incident,
  IngestResponse,
  LogEvent,
  RawLogEvent,
  Service,
  SimulationResponse,
} from "./api";

interface AppState {
  services: Service[];
  incidents: Incident[];
  logs: LogEvent[];
  dashboard: DashboardStats | null;
  loading: Record<string, boolean>;
  errors: Record<string, string | undefined>;
  theme: "dark" | "light";
  setTheme: (theme: "dark" | "light") => void;
  refresh: () => Promise<void>;
  acknowledgeIncident: (id: number) => Promise<void>;
  resolveIncident: (id: number) => Promise<void>;
  simulate: (seed?: number, totalEvents?: number) => Promise<SimulationResponse>;
  ingestLogs: (events: RawLogEvent[]) => Promise<IngestResponse>;
  ingestFile: (file: File) => Promise<IngestResponse>;
}

const AppContext = createContext<AppState | null>(null);

function messageFrom(error: unknown): string {
  if (error instanceof Error) return error.message;
  return "An unexpected request error occurred.";
}

function storedTheme(): "dark" | "light" {
  try {
    const value = window.localStorage?.getItem?.("opsradar-theme");
    return value === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [services, setServices] = useState<Service[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [dashboard, setDashboard] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string | undefined>>({});
  const [theme, setThemeState] = useState<"dark" | "light">(storedTheme);
  const initialLoadStarted = useRef(false);

  const setLoadingState = useCallback((key: string, value: boolean) => {
    setLoading((previous) => ({ ...previous, [key]: value }));
  }, []);
  const setErrorState = useCallback((key: string, value?: string) => {
    setErrors((previous) => ({ ...previous, [key]: value }));
  }, []);
  const setTheme = useCallback((value: "dark" | "light") => setThemeState(value), []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.classList.toggle("light", theme === "light");
    try {
      window.localStorage?.setItem?.("opsradar-theme", theme);
    } catch {
      // Storage can be unavailable in privacy modes; in-memory theming still works.
    }
  }, [theme]);

  const fetchServices = useCallback(async () => {
    setLoadingState("services", true);
    setErrorState("services");
    try {
      setServices((await apiService.services()).data);
    } catch (error) {
      setErrorState("services", messageFrom(error));
      throw error;
    } finally {
      setLoadingState("services", false);
    }
  }, [setErrorState, setLoadingState]);

  const fetchDashboard = useCallback(async () => {
    setLoadingState("dashboard", true);
    setErrorState("dashboard");
    try {
      setDashboard((await apiService.dashboard()).data);
    } catch (error) {
      setErrorState("dashboard", messageFrom(error));
      throw error;
    } finally {
      setLoadingState("dashboard", false);
    }
  }, [setErrorState, setLoadingState]);

  const fetchIncidents = useCallback(async () => {
    setLoadingState("incidents", true);
    setErrorState("incidents");
    try {
      setIncidents((await apiService.incidents()).data);
    } catch (error) {
      setErrorState("incidents", messageFrom(error));
      throw error;
    } finally {
      setLoadingState("incidents", false);
    }
  }, [setErrorState, setLoadingState]);

  const fetchLogs = useCallback(async () => {
    setLoadingState("logs", true);
    setErrorState("logs");
    try {
      setLogs((await apiService.logs({ limit: 100 })).data);
    } catch (error) {
      setErrorState("logs", messageFrom(error));
      throw error;
    } finally {
      setLoadingState("logs", false);
    }
  }, [setErrorState, setLoadingState]);

  const refresh = useCallback(async () => {
    await Promise.allSettled([
      fetchServices(),
      fetchDashboard(),
      fetchIncidents(),
      fetchLogs(),
    ]);
  }, [fetchServices, fetchDashboard, fetchIncidents, fetchLogs]);

  const updateIncident = useCallback(
    async (id: number, status: "acknowledged" | "resolved") => {
      const key = `incident-${id}`;
      setLoadingState(key, true);
      setErrorState("mutation");
      try {
        await apiService.updateIncident(id, status);
        await refresh();
      } catch (error) {
        setErrorState("mutation", messageFrom(error));
        throw error;
      } finally {
        setLoadingState(key, false);
      }
    },
    [refresh, setErrorState, setLoadingState]
  );

  const acknowledgeIncident = useCallback(
    (id: number) => updateIncident(id, "acknowledged"),
    [updateIncident]
  );
  const resolveIncident = useCallback(
    (id: number) => updateIncident(id, "resolved"),
    [updateIncident]
  );

  const simulate = useCallback(
    async (seed?: number, totalEvents?: number) => {
      setLoadingState("simulate", true);
      setErrorState("mutation");
      try {
        const response = await apiService.simulate(seed, totalEvents);
        await refresh();
        return response.data;
      } catch (error) {
        setErrorState("mutation", messageFrom(error));
        throw error;
      } finally {
        setLoadingState("simulate", false);
      }
    },
    [refresh, setErrorState, setLoadingState]
  );

  const runIngestion = useCallback(
    async (request: () => ReturnType<typeof apiService.ingestLogs>) => {
      setLoadingState("ingest", true);
      setErrorState("mutation");
      try {
        const response = await request();
        await refresh();
        return response.data;
      } catch (error) {
        setErrorState("mutation", messageFrom(error));
        throw error;
      } finally {
        setLoadingState("ingest", false);
      }
    },
    [refresh, setErrorState, setLoadingState]
  );

  const ingestLogs = useCallback(
    (events: RawLogEvent[]) => runIngestion(() => apiService.ingestLogs(events)),
    [runIngestion]
  );
  const ingestFile = useCallback(
    (file: File) => runIngestion(() => apiService.ingestFile(file)),
    [runIngestion]
  );

  useEffect(() => {
    if (initialLoadStarted.current) return;
    initialLoadStarted.current = true;
    void refresh();
  }, [refresh]);

  const value = useMemo(
    () => ({
      services, incidents, logs, dashboard, loading, errors, theme, setTheme, refresh,
      acknowledgeIncident, resolveIncident, simulate, ingestLogs, ingestFile,
    }),
    [
      services, incidents, logs, dashboard, loading, errors, theme, setTheme, refresh,
      acknowledgeIncident, resolveIncident, simulate, ingestLogs, ingestFile,
    ]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error("useApp must be used within AppProvider");
  return context;
}
