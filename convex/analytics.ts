import { query } from "./_generated/server";
import { v } from "convex/values";

// Brand analytics computed live from stored data. One round-trip → everything
// the dashboard + analytics page need. No external analytics vendor.
export const summary = query({
  args: { brandId: v.id("brands") },
  handler: async (ctx, { brandId }) => {
    const [mentions, insights, campaigns, packets, sessions] = await Promise.all([
      ctx.db.query("mentions").withIndex("by_brand", (q) => q.eq("brandId", brandId)).collect(),
      ctx.db.query("insights").withIndex("by_brand", (q) => q.eq("brandId", brandId)).collect(),
      ctx.db.query("campaigns").withIndex("by_brand", (q) => q.eq("brandId", brandId)).collect(),
      ctx.db.query("packets").withIndex("by_brand", (q) => q.eq("brandId", brandId)).collect(),
      ctx.db.query("sessions").withIndex("by_brand", (q) => q.eq("brandId", brandId)).collect(),
    ]);

    // Mentions by platform.
    const byPlatform: Record<string, number> = {};
    for (const m of mentions) byPlatform[m.platform] = (byPlatform[m.platform] ?? 0) + 1;

    // Mention volume + avg score per day (last 14 days).
    const DAY = 86_400_000;
    const today = Math.floor(Date.now() / DAY);
    const days: { day: string; count: number; avgScore: number; highSignal: number }[] = [];
    for (let i = 13; i >= 0; i--) {
      const dayIdx = today - i;
      const inDay = mentions.filter((m) => Math.floor(m.ts / DAY) === dayIdx);
      const avg = inDay.length
        ? inDay.reduce((a, m) => a + m.score, 0) / inDay.length
        : 0;
      days.push({
        day: new Date(dayIdx * DAY).toISOString().slice(5, 10),
        count: inDay.length,
        avgScore: Math.round(avg * 100) / 100,
        highSignal: inDay.filter((m) => m.highSignal).length,
      });
    }

    // Insights by severity.
    const bySeverity: Record<string, number> = { risk: 0, opportunity: 0, info: 0 };
    for (const it of insights) {
      const s = it.severity ?? "info";
      bySeverity[s] = (bySeverity[s] ?? 0) + 1;
    }

    // Campaign status counts.
    const campaignStatus: Record<string, number> = {};
    for (const c of campaigns) campaignStatus[c.status] = (campaignStatus[c.status] ?? 0) + 1;

    return {
      totals: {
        mentions: mentions.length,
        highSignal: mentions.filter((m) => m.highSignal).length,
        insights: insights.length,
        campaigns: campaigns.length,
        packets: packets.length,
        sessions: sessions.length,
      },
      byPlatform,
      bySeverity,
      campaignStatus,
      timeline: days,
    };
  },
});
