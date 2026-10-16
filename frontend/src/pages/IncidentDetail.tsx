import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useApp } from "../lib/store";
import { Incident } from "../lib/api";
import { AlertCircle, Clock, List, Terminal } from "lucide-react";
import { Button, Badge, Card, CardContent, CardHeader, CardTitle } from "../components/ui";
import { formatRelativeTime, severityColor } from "../lib/utils";

export function IncidentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { incidents, acknowledgeIncident, resolveIncident, loading } = useApp();
  const [incident, setIncident] = useState<Incident | null>(null);

  useEffect(() => {
    const inc = incidents.find((i) => i.id === Number(id));
    if (inc) setIncident(inc);
  }, [incidents, id]);

  if (!incident && loading.incidents) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
        Loading incident…
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 text-muted-foreground">
        <AlertCircle className="h-8 w-8" />
        <p>Incident not found.</p>
        <Button variant="outline" onClick={() => navigate("/incidents")}>Back to incidents</Button>
      </div>
    );
  }

  const goBack = () => navigate(-1);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={goBack}>
          <AlertCircle className="w-4 h-4 mr-1" /> Back
        </Button>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between pb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge
                variant={
                  incident.severity === "CRITICAL"
                    ? "destructive"
                    : incident.severity === "WARNING"
                      ? "outline"
                      : "default"
                }
                className={severityColor(incident.severity)}
              >
                {incident.severity}
              </Badge>
              <Badge variant="outline">
                {incident.status}
              </Badge>
            </div>
            <CardTitle>{incident.title}</CardTitle>
            <div className="text-xs text-muted-foreground mt-1">
              {incident.service} · {incident.environment} · {incident.event_count} events ·
              {formatRelativeTime(incident.first_seen)} first seen
            </div>
          </div>
          <div className="flex gap-2">
            {incident.status === "open" && (
              <>
                <Button size="sm" onClick={() => void acknowledgeIncident(incident.id).catch(() => undefined)} disabled={loading[`incident-${incident.id}`]}>
                  Acknowledge
                </Button>
                <Button size="sm" variant="outline" onClick={() => void resolveIncident(incident.id).catch(() => undefined)} disabled={loading[`incident-${incident.id}`]}>
                  Resolve
                </Button>
              </>
            )}
            {incident.status !== "open" && (
              <Button size="sm" variant="ghost" disabled className="opacity-50">
                {incident.status}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Root cause */}
          <Card className="col-span-1 md:col-span-2 p-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle className="w-5 h-5 text-destructive" />
              <h3 className="font-semibold">Possible Root Cause</h3>
              <span className="ml-auto text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400">
                Speculative — {incident.root_cause_confidence || "not confirmed"}
              </span>
            </div>
            <p className="text-sm leading-relaxed">{incident.root_cause}</p>
          </Card>

          {/* Confidence */}
          <Card className="col-span-1 md:col-span-1 p-4">
            <div className="text-xs text-muted-foreground mb-2">Confidence</div>
            <div className="text-3xl font-bold">
              {Math.round((incident.confidence || 0) * 100)}%
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              Rule-based detection confidence. Not an AI guess.
            </div>
          </Card>

          {/* Suggested steps */}
          <Card className="col-span-1 md:col-span-2 p-4">
            <div className="flex items-center gap-2 mb-3">
              <List className="w-5 h-5" />
              <h3 className="font-semibold">Suggested Investigation Steps</h3>
            </div>
            <ol className="list-decimal list-inside text-sm space-y-1 text-muted-foreground">
              {(incident.suggested_steps || []).map((s: string, i: number) => (
                <li key={i}>{s}</li>
              ))}
            </ol>
          </Card>

          {/* Remediation */}
          <Card className="col-span-1 md:col-span-2 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Terminal className="w-5 h-5" />
              <h3 className="font-semibold">Suggested Remediation</h3>
              <span className="ml-auto text-[10px] px-2 py-0.5 rounded bg-destructive/10 text-destructive">
                Manual only — not executed
              </span>
            </div>
            <ol className="list-decimal list-inside text-sm space-y-1 text-muted-foreground">
              {(incident.suggested_remediation || []).map((s: string, i: number) => (
                <li key={i}>{s}</li>
              ))}
            </ol>
          </Card>
        </CardContent>
      </Card>

      {/* Related events */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            <CardTitle>Timeline of Related Events</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="border-t">
            {[
              { t: incident.first_seen, m: "First related event detected" },
              { t: incident.last_seen, m: "Most recent related event" },
            ].map((e, i) => (
              <div key={i} className="border-b p-3 flex gap-3">
                <div className="w-8 h-8 rounded-full border flex items-center justify-center text-xs font-bold shrink-0">
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium">{e.m}</div>
                  <div className="text-xs text-muted-foreground">
                    {formatRelativeTime(e.t)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
