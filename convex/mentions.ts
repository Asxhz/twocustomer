import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Insert a mention, deduped on (brandId, externalId). Returns the id or null if dup.
export const insertMention = mutation({
  args: {
    brandId: v.string(), // slug from the agent; resolved to a brand doc
    platform: v.string(),
    externalId: v.string(),
    author: v.optional(v.string()),
    text: v.string(),
    url: v.optional(v.string()),
    score: v.number(),
    highSignal: v.boolean(),
    ts: v.number(),
  },
  handler: async (ctx, args) => {
    const { brandId, ...rest } = args;
    const brand = await ctx.db
      .query("brands")
      .withIndex("by_slug", (q) => q.eq("slug", brandId))
      .first();
    if (!brand) return null;
    const existing = await ctx.db
      .query("mentions")
      .withIndex("by_brand_external", (q) =>
        q.eq("brandId", brand._id).eq("externalId", rest.externalId),
      )
      .first();
    if (existing) return null;
    return await ctx.db.insert("mentions", { brandId: brand._id, ...rest });
  },
});

export const listMentions = query({
  args: { brandId: v.id("brands"), limit: v.optional(v.number()) },
  handler: async (ctx, { brandId, limit }) => {
    const rows = await ctx.db
      .query("mentions")
      .withIndex("by_brand", (q) => q.eq("brandId", brandId))
      .order("desc")
      .take(limit ?? 50);
    return rows;
  },
});
