import { useState } from "react";
import { Link } from "react-router-dom";
import { useApp } from "../lib/store";
import { Play, Filter } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
} from "../components/ui";
import { severityColor } from "../lib/utils";

export function Incidents() {
  const { incidents, acknowledgeIncident, resolveIncident, loading, simulate } = useApp();
  const [statusFilter, setStatusFilter] = useState("");

  const filtered = incidents.filter(
    (i) => !statusFilter || i.status === statusFilter
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Incidents</h1>
          <p className="text-muted-foreground">
            Detected, correlated, and triaged incidents
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => simulate()}
            disabled={loading.simulate}
            className="flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            {loading.simulate ? "Simulating…" : "Simulate Incident"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <Card className="overflow-hidden">
            <CardHeader className="pb-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 mr-1" />
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="bg-transparent border-none text-sm focus:ring-0"
                  >
                    <option value="">All statuses</option>
                    <option value="open">Open</option>
                    <option value="acknowledged">Acknowledged</option>
                    <option value="resolved">Resolved</option>
                  </select>
                </div>
                <span className="text-xs text-muted-foreground">
                  {filtered.length} incidents
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto border-b border-t">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b text-muted-foreground">
                      <th className="px-4 py-3 font-medium">Title</th>
                      <th className="px-4 py-3 font-medium text-center">Severity</th>
                      <th className="px-4 py-3 font-medium">Service</th>
                      <th className="px-4 py-3 font-medium text-center">Events</th>
                      <th className="px-4 py-3 font-medium text-center">Status</th>
                      <th className="px-4 py-3 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {filtered.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-4 py-12 text-center text-muted-foreground">
                          No incidents found
                        </td>
                      </tr>
                    ) : (
                      filtered.map((inc) => (
                        <tr key={inc.id} className="group hover:bg-muted/50">
                          <td className="px-4 py-3">
                            <Link
                              to={`/incidents/${inc.id}`}
                              className="font-medium text-primary hover:underline truncate block max-w-[300px]"
                            >
                              {inc.title}
                            </Link>
                            <div className="text-[10px] text-muted-foreground mt-0.5 truncate">
                              {inc.signature}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <Badge
                              variant={
                                inc.severity === "CRITICAL"
                                  ? "destructive"
                                  : inc.severity === "WARNING"
                                    ? "outline"
                                    : "default"
                              }
                              className={severityColor(inc.severity)}
                            >
                              {inc.severity}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 font-mono text-xs">{inc.service}</td>
                          <td className="px-4 py-3 text-center text-muted-foreground">
                            {inc.event_count}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold ${
                                inc.status === "open"
                                  ? "bg-destructive/10 text-destructive border border-destructive/20"
                                  : inc.status === "acknowledged"
                                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                    : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              }`}
                            >
                              {inc.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            {inc.status === "open" ? (
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => acknowledgeIncident(inc.id)}
                                  className="mr-2 h-7 px-2 text-xs"
                                >
                                  Acknowledge
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => resolveIncident(inc.id)}
                                  className="h-7 px-2 text-xs"
                                >
                                  Resolve
                                </Button>
                              </>
                            ) : (
                              <Button
                                size="sm"
                                variant="ghost"
                                disabled
                                className="h-7 px-2 text-xs opacity-50"
                              >
                                {inc.status}
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-1">
          <Card className="p-4">
            <CardHeader>
              <CardTitle className="text-sm">Quick Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Open</span>
                <span className="text-sm font-bold text-destructive">
                  {incidents.filter((i) => i.status === "open").length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Critical</span>
                <span className="text-sm font-bold text-destructive">
                  {incidents.filter((i) => i.severity === "CRITICAL").length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Acknowledged</span>
                <span className="text-sm font-bold text-amber-400">
                  {incidents.filter((i) => i.status === "acknowledged").length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Resolved</span>
                <span className="text-sm font-bold text-emerald-400">
                  {incidents.filter((i) => i.status === "resolved").length}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
