"use client";

import { useMemo } from "react";
import { ReactFlow, Background, Controls, type Node, type Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

interface GNode {
  id: string;
  type: string; // source | insight | campaign | packet
  label: string;
  meta?: string;
}
interface GEdge {
  id: string;
  source: string;
  target: string;
}

// Four columns: source → insight → campaign/packet (actions share the last column).
const COL: Record<string, number> = { source: 0, insight: 1, campaign: 2, packet: 2 };
const COLORS: Record<string, string> = {
  source: "#1e3a8a",
  insight: "#2563eb",
  campaign: "#0ea5e9",
  packet: "#0ea5e9",
};

export default function SourceGraph({ nodes, edges }: { nodes: GNode[]; edges: GEdge[] }) {
  const rfNodes: Node[] = useMemo(() => {
    const perCol: Record<number, number> = {};
    return nodes.map((n) => {
      const col = COL[n.type] ?? 3;
      const row = (perCol[col] = (perCol[col] ?? 0) + 1);
      return {
        id: n.id,
        position: { x: col * 280, y: row * 90 },
        data: { label: `${n.label}${n.meta ? ` · ${n.meta}` : ""}` },
        style: {
          background: COLORS[n.type] ?? "#334155",
          color: "white",
          border: "1px solid rgba(255,255,255,0.15)",
          borderRadius: 10,
          fontSize: 11,
          width: 220,
          padding: 8,
        },
      };
    });
  }, [nodes]);

  const rfEdges: Edge[] = useMemo(
    () =>
      edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        animated: true,
        style: { stroke: "rgba(96,165,250,0.5)" },
      })),
    [edges],
  );

  const legend = [
    ["source", "Sources"],
    ["insight", "Insights"],
    ["campaign", "Actions"],
  ];

  return (
    <div className="relative h-[70vh] rounded-xl border border-white/10 bg-white/[0.02]">
      <div className="absolute left-3 top-3 z-10 flex gap-3 rounded-lg border border-white/10 bg-black/60 px-3 py-1.5 text-xs backdrop-blur">
        {legend.map(([k, label]) => (
          <span key={k} className="flex items-center gap-1.5 text-white/70">
            <span className="h-2 w-2 rounded-full" style={{ background: COLORS[k] }} />
            {label}
          </span>
        ))}
      </div>
      <ReactFlow nodes={rfNodes} edges={rfEdges} fitView proOptions={{ hideAttribution: true }}>
        <Background color="rgba(255,255,255,0.08)" />
        <Controls />
      </ReactFlow>
    </div>
  );
}
