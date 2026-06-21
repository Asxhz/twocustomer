"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import type { AnalyticsSummary } from "@/lib/convexHttp";

const BLUE = "#3b82f6";
const BLUE_SOFT = "#60a5fa";
const SEV: Record<string, string> = {
  risk: "#f87171",
  opportunity: "#3b82f6",
  info: "#94a3b8",
};

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <h3 className="mb-3 text-sm font-medium text-white/70">{title}</h3>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          {children as React.ReactElement}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

const tooltipStyle = {
  background: "#0a0a0a",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  fontSize: 12,
};

export default function AnalyticsCharts({ data }: { data: AnalyticsSummary }) {
  const platform = Object.entries(data.byPlatform).map(([name, value]) => ({ name, value }));
  const severity = Object.entries(data.bySeverity)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value }));
  const campaigns = Object.entries(data.campaignStatus).map(([name, value]) => ({ name, value }));

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card title="Mention volume (last 14 days)">
        <AreaChart data={data.timeline}>
          <defs>
            <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={BLUE} stopOpacity={0.5} />
              <stop offset="95%" stopColor={BLUE} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="day" tick={{ fill: "#888", fontSize: 11 }} />
          <YAxis tick={{ fill: "#888", fontSize: 11 }} allowDecimals={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Area type="monotone" dataKey="count" stroke={BLUE} fill="url(#g)" name="mentions" />
          <Area type="monotone" dataKey="highSignal" stroke={BLUE_SOFT} fill="none" name="high-signal" />
        </AreaChart>
      </Card>

      <Card title="Mentions by platform">
        <BarChart data={platform}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="name" tick={{ fill: "#888", fontSize: 11 }} />
          <YAxis tick={{ fill: "#888", fontSize: 11 }} allowDecimals={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
          <Bar dataKey="value" fill={BLUE} radius={[4, 4, 0, 0]} name="mentions" />
        </BarChart>
      </Card>

      <Card title="Insights by severity">
        <PieChart>
          <Pie data={severity} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75} paddingAngle={3}>
            {severity.map((s) => (
              <Cell key={s.name} fill={SEV[s.name] ?? BLUE} />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
        </PieChart>
      </Card>

      <Card title="Campaign status">
        <BarChart data={campaigns} layout="vertical">
          <CartesianGrid stroke="rgba(255,255,255,0.06)" />
          <XAxis type="number" tick={{ fill: "#888", fontSize: 11 }} allowDecimals={false} />
          <YAxis type="category" dataKey="name" tick={{ fill: "#888", fontSize: 11 }} width={70} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
          <Bar dataKey="value" fill={BLUE_SOFT} radius={[0, 4, 4, 0]} name="campaigns" />
        </BarChart>
      </Card>
    </div>
  );
}
