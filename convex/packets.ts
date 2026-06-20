import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const add = mutation({
  args: {
    brandId: v.string(),
    title: v.string(),
    summary: v.string(),
    evidence: v.optional(v.array(v.string())),
    recommendedAction: v.optional(v.string()),
    artifact: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { brandId, ...rest } = args;
    // brandId arrives as a slug/string from the agent; resolve to a brand doc.
    const brand = await ctx.db
      .query("brands")
      .withIndex("by_slug", (q) => q.eq("slug", brandId))
      .first();
    if (!brand) return null;
    return ctx.db.insert("packets", {
      brandId: brand._id,
      ...rest,
      createdAt: Date.now(),
    });
  },
});

export const list = query({
  args: { brandId: v.id("brands"), limit: v.optional(v.number()) },
  handler: async (ctx, { brandId, limit }) =>
    ctx.db
      .query("packets")
      .withIndex("by_brand", (q) => q.eq("brandId", brandId))
      .order("desc")
      .take(limit ?? 25),
});
