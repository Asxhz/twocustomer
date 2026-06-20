import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const add = mutation({
  args: {
    brandId: v.string(), // slug from the agent; resolved to a brand doc
    brief: v.string(),
    body: v.string(),
    status: v.string(),
  },
  handler: async (ctx, args) => {
    const { brandId, ...rest } = args;
    const brand = await ctx.db
      .query("brands")
      .withIndex("by_slug", (q) => q.eq("slug", brandId))
      .first();
    if (!brand) return null;
    return ctx.db.insert("campaigns", {
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
      .query("campaigns")
      .withIndex("by_brand", (q) => q.eq("brandId", brandId))
      .order("desc")
      .take(limit ?? 25),
});
