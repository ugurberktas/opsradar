import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "../ui";

const COLORS = ["#38bdf8", "#fbbf24", "#f87171"];

export function SeverityDonut({
  distribution,
}: {
  distribution: Record<string, number>;
}) {
  const data = [
    { name: "CRITICAL", value: distribution.CRITICAL || 0, color: COLORS[2] },
    { name: "WARNING", value: distribution.WARNING || 0, color: COLORS[1] },
    { name: "INFO", value: distribution.INFO || 0, color: COLORS[0] },
  ];
  const total = data.reduce((a, b) => a + b.value, 0);
  return (
    <Card>
      <CardHeader>
        <CardTitle>Incident Severity</CardTitle>
      </CardHeader>
      <CardContent className="pb-8">
        <div className="flex flex-col items-center justify-center">
          <div className="text-2xl font-bold">{total}</div>
          <div className="text-xs text-muted-foreground">total active</div>
        </div>
        <div className="h-48 w-full mt-6">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                fill="#888"
                dataKey="value"
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ border: "1px solid #334155", background: "#0f172a", color: "#f8fafc" }}
                formatter={(value) => `${value} incidents`}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex justify-between mt-4 text-xs text-muted-foreground">
          {data.map((d) => (
            <div key={d.name} className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
              {d.name}: {d.value}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
