import { query } from "./_generated/server";
import { v } from "convex/values";

// The source -> insight -> action graph for one brand. Returns nodes + edges
// ready to drop into React Flow. Edges link mentions to the insights that cite
// them (insights.sourceMentionIds), and insights to campaigns/packets.
export const forBrand = query({
  args: { brandId: v.id("brands") },
  handler: async (ctx, { brandId }) => {
    const [mentions, insights, campaigns, packets] = await Promise.all([
      ctx.db.query("mentions").withIndex("by_brand", (q) => q.eq("brandId", brandId)).order("desc").take(40),
      ctx.db.query("insights").withIndex("by_brand", (q) => q.eq("brandId", brandId)).collect(),
      ctx.db.query("campaigns").withIndex("by_brand", (q) => q.eq("brandId", brandId)).collect(),
      ctx.db.query("packets").withIndex("by_brand", (q) => q.eq("brandId", brandId)).collect(),
    ]);

    type Node = { id: string; type: string; label: string; meta?: string };
    type Edge = { id: string; source: string; target: string };
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    for (const m of mentions) {
      nodes.push({
        id: `m_${m._id}`,
        type: "source",
        label: m.platform,
        meta: (m.text ?? "").slice(0, 80),
      });
    }
    for (const it of insights) {
      nodes.push({
        id: `i_${it._id}`,
        type: "insight",
        label: it.title,
        meta: it.severity,
      });
      for (const mid of it.sourceMentionIds ?? []) {
        edges.push({ id: `e_${mid}_${it._id}`, source: `m_${mid}`, target: `i_${it._id}` });
      }
    }
    // Insights -> campaigns / packets (best-effort: link all to all when no
    // explicit FK exists — keeps the action layer visible).
    for (const c of campaigns) {
      nodes.push({ id: `c_${c._id}`, type: "campaign", label: c.brief.slice(0, 40), meta: c.status });
      for (const it of insights) edges.push({ id: `ec_${it._id}_${c._id}`, source: `i_${it._id}`, target: `c_${c._id}` });
    }
    for (const p of packets) {
      nodes.push({ id: `p_${p._id}`, type: "packet", label: p.title, meta: p.recommendedAction });
      for (const it of insights) edges.push({ id: `ep_${it._id}_${p._id}`, source: `i_${it._id}`, target: `p_${p._id}` });
    }

    return { nodes, edges };
  },
});
