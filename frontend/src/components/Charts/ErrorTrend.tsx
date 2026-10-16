import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "../ui";

export function ErrorTrend({ data }: { data: Array<{ ts: string; count: number }> }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Error Trend (24h)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="ts"
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickFormatter={(v: string) => {
                  const d = new Date(v);
                  return d.getHours().toString().padStart(2, "0") + ":00";
                }}
              />
              <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
              <Tooltip
                contentStyle={{ border: "1px solid #e2e8f0", background: "#fff", color: "#0f172a" }}
                labelFormatter={(v) => new Date(v as string).getHours() + ":00"}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#38bdf8"
                strokeWidth={2}
                dot={false}
                strokeDasharray="6 3"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
