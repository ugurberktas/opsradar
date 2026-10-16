import { useApp } from "../lib/store";
import { StatCard } from "../components/ui";
import { LayoutDashboard, AlertTriangle, RefreshCw } from "lucide-react";
import { ErrorTrend } from "../components/Charts/ErrorTrend";
import { SeverityDonut } from "../components/Charts/SeverityDonut";
import { ServiceHealth } from "../components/Charts/ServiceHealth";
import { formatRelativeTime } from "../lib/utils";

export function Dashboard() {
  const { dashboard, loading, refresh } = useApp();

  if (!dashboard) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-2 animate-pulse">
          <div className="w-24 h-24 rounded-full bg-muted/50" />
          <p className="text-muted-foreground">Loading dashboard…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Infrastructure health and incident overview
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => void refresh()}
            disabled={loading.dashboard}
            className="flex items-center gap-2 px-3 py-2 rounded-md border bg-secondary text-secondary-foreground hover:bg-secondary/80 text-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading.dashboard ? "animate-spin" : ""}`} /> Refresh
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Services"
          value={dashboard.total_services}
          icon={LayoutDashboard}
        />
        <StatCard
          title="Active Incidents"
          value={dashboard.active_incidents}
          icon={AlertTriangle}
          delta={
            dashboard.incidents_by_status.open > 0
              ? `${dashboard.incidents_by_status.open} open`
              : "All clear"
          }
        />
        <StatCard
          title="Healthy"
          value={dashboard.healthy_services}
          delta="services"
        />
        <StatCard
          title="Degraded"
          value={dashboard.warning_services + dashboard.critical_services}
          delta="warning + critical"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: trend + severity */}
        <div className="lg:col-span-2 grid grid-cols-1 gap-6">
          <ErrorTrend data={dashboard.error_trend} />
          <SeverityDonut distribution={dashboard.incidents_by_severity} />
        </div>

        {/* Right: service health + recent events */}
        <div className="lg:col-span-1 grid grid-cols-1 gap-6">
          <ServiceHealth services={dashboard.service_health} />
          <div className="flex flex-col gap-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Recent Events
            </h2>
            <div className="space-y-2 overflow-hidden max-h-64">
              {dashboard.recent_events.slice(0, 8).map((e) => (
                <div
                  key={e.id}
                  className="flex items-start gap-2 p-2 rounded-lg border bg-muted/50"
                >
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded ${
                      e.level === "ERROR" || e.level === "FATAL"
                        ? "bg-destructive/10 text-destructive"
                        : e.level === "WARN"
                          ? "bg-amber-500/10 text-amber-400"
                          : "bg-primary/10 text-primary"
                    }`}
                  >
                    {e.level}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium truncate">{e.service}</div>
                    <div className="text-xs text-muted-foreground truncate">
                      {e.message}
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">
                      {formatRelativeTime(e.timestamp)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
