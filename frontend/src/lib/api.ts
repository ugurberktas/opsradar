import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

export interface Service {
  id: number;
  name: string;
  environment: string;
  status: string;
  last_heartbeat: string | null;
  log_count: number;
  incident_count: number;
}

export interface LogEvent {
  id: number;
  service: string;
  environment: string;
  timestamp: string;
  level: string;
  message: string;
  service_id: number | null;
  signature: string | null;
  redacted: boolean;
}

export interface Incident {
  id: number;
  title: string;
  severity: string;
  status: string;
  service: string;
  environment: string;
  signature: string;
  event_count: number;
  confidence: number;
  root_cause: string | null;
  root_cause_confidence: string | null;
  suggested_steps: string[];
  suggested_remediation: string[];
  first_seen: string;
  last_seen: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  created_at: string;
  related_log_count: number;
}

export interface DashboardStats {
  total_services: number;
  healthy_services: number;
  warning_services: number;
  critical_services: number;
  active_incidents: number;
  incidents_by_severity: Record<string, number>;
  incidents_by_status: Record<string, number>;
  recent_events: LogEvent[];
  error_trend: Array<{ ts: string; count: number }>;
  service_health: Array<{ name: string; environment: string; status: string }>;
}

export interface SimulationResponse {
  events_generated: number;
  incidents_detected: number;
  scenario: string;
}

export const apiService = {
  health: () => api.get("/api/health"),
  services: () => api.get<Service[]>("/api/services"),
  dashboard: () => api.get<DashboardStats>("/api/dashboard"),
  logs: (params?: { service?: string; level?: string; search?: string; limit?: number }) =>
    api.get<LogEvent[]>("/api/logs", { params }),
  ingestLogs: (events: any[]) => api.post("/api/logs/ingest", { events }),
  ingestFile: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/api/logs/ingest/file", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  incidents: (params?: { status?: string; severity?: string; service?: string }) =>
    api.get<Incident[]>("/api/incidents", { params }),
  incident: (id: number) => api.get<Incident>(`/api/incidents/${id}`),
  updateIncident: (id: number, status: string) =>
    api.patch<Incident>(`/api/incidents/${id}`, { status }),
  simulate: (seed?: number, total_events?: number) =>
    api.post<SimulationResponse>("/api/simulate", {}, { params: { seed, total_events } }),
};
