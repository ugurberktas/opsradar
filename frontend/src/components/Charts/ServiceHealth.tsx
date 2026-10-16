import { Card, CardContent, CardHeader, CardTitle } from "../ui";

export function ServiceHealth({
  services,
}: {
  services: Array<{ name: string; environment: string; status: string }>;
}) {
  const counts = services.reduce(
    (acc, s) => {
      acc[s.status] = (acc[s.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );
  return (
    <Card>
      <CardHeader>
        <CardTitle>Service Health</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2">
          {[
            { label: "Healthy", key: "healthy", color: "text-emerald-400" },
            { label: "Warning", key: "warning", color: "text-amber-400" },
            { label: "Critical", key: "critical", color: "text-destructive" },
          ].map((cat) => (
            <div
              key={cat.key}
              className="flex items-center justify-between px-3 py-2 rounded-lg border"
            >
              <span className="text-sm">{cat.label}</span>
              <span className={`text-sm font-bold ${counts[cat.key] === 0 ? "text-muted-foreground" : cat.color}`}>
                {counts[cat.key] || 0}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
