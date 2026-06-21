import type { DataSource } from "@/lib/convexHttp";

// Honest data-provenance badge. "live" = real Convex rows; "empty" = connected
// but nothing yet; "unavailable" = agent/Convex offline; "demo" = local sample.
export default function LiveBadge({ source }: { source: DataSource }) {
  const map: Record<DataSource, { label: string; cls: string }> = {
    live: { label: "live", cls: "bg-accent/15 text-accent-soft" },
    empty: { label: "no data yet", cls: "bg-white/10 text-white/50" },
    unavailable: { label: "backend offline", cls: "bg-red-500/15 text-red-300" },
  };
  const { label, cls } = map[source];
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs ${cls}`}>{label}</span>
  );
}
