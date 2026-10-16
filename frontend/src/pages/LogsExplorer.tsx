import { useState } from "react";
import { useApp } from "../lib/store";
import { Upload } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
} from "../components/ui";
import { formatRelativeTime } from "../lib/utils";

export function LogsExplorer() {
  const { logs, loading } = useApp();
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [serviceFilter, setServiceFilter] = useState("");

  const services = [...new Set(logs.map((l) => l.service))].sort();

  const filtered = logs.filter(
    (l) =>
      (!search ||
        l.message.toLowerCase().includes(search.toLowerCase()) ||
        l.service.toLowerCase().includes(search.toLowerCase())) &&
      (!levelFilter || l.level === levelFilter) &&
      (!serviceFilter || l.service === serviceFilter)
  );

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const form = new FormData();
    form.append("file", f);
    const res = await fetch(`${import.meta.env.VITE_API_BASE || ""}/api/logs/ingest/file`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new Error("Upload failed");
    const data = await res.json();
    alert(`Ingested ${data.ingested} events`);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Logs Explorer</h1>
          <p className="text-muted-foreground">
            Search, filter, and ingest infrastructure logs
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => (document.getElementById("file-input") as HTMLInputElement).click()}>
            <Upload className="w-4 h-4 mr-2" /> Upload JSONL
          </Button>
          <input
            id="file-input"
            type="file"
            accept=".jsonl,.log,.txt"
            onChange={handleFile}
            className="hidden"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-3">
          <Card className="p-4">
            <CardHeader>
              <CardTitle className="text-sm">Filters</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-xs block mb-1 text-muted-foreground">Search</label>
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="message or service…"
                />
              </div>
              <div>
                <label className="text-xs block mb-1 text-muted-foreground">Level</label>
                <select
                  value={levelFilter}
                  onChange={(e) => setLevelFilter(e.target.value)}
                  className="w-full rounded border bg-input px-2 py-1.5 text-sm"
                >
                  <option value="">All</option>
                  <option value="ERROR">ERROR</option>
                  <option value="WARN">WARN</option>
                  <option value="INFO">INFO</option>
                  <option value="FATAL">FATAL</option>
                </select>
              </div>
              <div>
                <label className="text-xs block mb-1 text-muted-foreground">Service</label>
                <select
                  value={serviceFilter}
                  onChange={(e) => setServiceFilter(e.target.value)}
                  className="w-full rounded border bg-input px-2 py-1.5 text-sm"
                >
                  <option value="">All</option>
                  {services.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                variant="outline"
                onClick={() => {
                  setSearch("");
                  setLevelFilter("");
                  setServiceFilter("");
                }}
                className="w-full"
              >
                Clear filters
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-9">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle>Log Events ({filtered.length} of {logs.length})</CardTitle>
              <div className="flex gap-1">
                <span className="text-[10px] font-mono text-muted-foreground">
                  {loading.ingest ? "ingesting…" : "ready"}
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto border-b">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b text-muted-foreground">
                      <th className="px-4 py-3 font-medium">Time</th>
                      <th className="px-4 py-3 font-medium">Service</th>
                      <th className="px-4 py-3 font-medium">Env</th>
                      <th className="px-4 py-3 font-medium">Level</th>
                      <th className="px-4 py-3 font-medium w-1/3">Message</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                          No log events found
                        </td>
                      </tr>
                    ) : (
                      filtered.slice(0, 200).map((e) => (
                        <tr key={e.id} className="border-b hover:bg-muted/50 group">
                          <td className="px-4 py-2 text-xs font-mono text-muted-foreground">
                            {formatRelativeTime(e.timestamp)}
                          </td>
                          <td className="px-4 py-2 text-xs font-medium">{e.service}</td>
                          <td className="px-4 py-2 text-xs">{e.environment}</td>
                          <td className="px-4 py-2 text-xs">
                            <span
                              className={`px-1.5 py-0.5 rounded text-xs font-bold ${
                                e.level === "ERROR" || e.level === "FATAL"
                                  ? "bg-destructive/10 text-destructive"
                                  : e.level === "WARN"
                                    ? "bg-amber-500/10 text-amber-400"
                                    : "bg-primary/10 text-primary"
                              }`}
                            >
                              {e.level}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-xs truncate max-w-[400px] font-mono">
                            {e.message}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              {filtered.length > 200 && (
                <div className="px-4 py-2 text-xs text-muted-foreground text-center">
                  Showing first 200 of {filtered.length} matching events
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
