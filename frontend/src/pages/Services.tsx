import { useApp } from "../lib/store";
import { Link } from "react-router-dom";
import { Server } from "lucide-react";
import { Badge } from "../components/ui";
import { statusColor } from "../lib/utils";

export function Services() {
  const { services, incidents } = useApp();

  // enrich with incident counts per severity
  const enriched = services.map((s) => {
    const incs = incidents.filter((i) => i.service === s.name && i.status === "open");
    return { ...s, openIncidents: incs.length };
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Services</h1>
        <p className="text-muted-foreground">
          Monitored microservices and their health
        </p>
      </div>

      <div className="overflow-x-auto border border-border rounded-xl">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b text-muted-foreground">
              <th className="px-4 py-3 font-medium">Service</th>
              <th className="px-4 py-3 font-medium">Environment</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium text-center">Open Incidents</th>
              <th className="px-4 py-3 font-medium text-center">Logs</th>
              <th className="px-4 py-3 font-medium text-right">Last Heartbeat</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {enriched.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-muted-foreground">
                  No services found
                </td>
              </tr>
            ) : (
              enriched.map((s) => (
                <tr key={s.id} className="group hover:bg-muted/50">
                  <td className="px-4 py-3">
                    <Link
                      to={`/incidents?service=${encodeURIComponent(s.name)}`}
                      className="font-medium text-primary hover:underline truncate block max-w-[200px]"
                    >
                      <div className="flex items-center gap-2">
                        <Server className="w-4 h-4" />
                        {s.name}
                      </div>
                    </Link>
                    <div className="text-[10px] text-muted-foreground truncate">
                      {s.environment}
                    </div>
                  </td>
                  <td className="px-4 py-3">{s.environment}</td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className={statusColor(s.status)}>
                      {s.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <Badge variant="outline">
                      {s.openIncidents}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-center text-muted-foreground font-mono text-xs">
                    {s.log_count}
                  </td>
                  <td className="px-4 py-3 text-right text-xs text-muted-foreground">
                    {s.last_heartbeat ? new Date(s.last_heartbeat).toLocaleString() : "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
