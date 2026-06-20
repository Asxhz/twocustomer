import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Create-or-return a brand by slug (idempotent seed).
export const upsert = mutation({
  args: {
    name: v.string(),
    slug: v.string(),
    terms: v.array(v.string()),
    handles: v.optional(
      v.object({
        x: v.optional(v.string()),
        reddit: v.optional(v.string()),
        linkedin: v.optional(v.string()),
      }),
    ),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("brands")
      .withIndex("by_slug", (q) => q.eq("slug", args.slug))
      .first();
    if (existing) return existing._id;
    return await ctx.db.insert("brands", { ...args, createdAt: Date.now() });
  },
});

export const getBySlug = query({
  args: { slug: v.string() },
  handler: async (ctx, { slug }) =>
    ctx.db
      .query("brands")
      .withIndex("by_slug", (q) => q.eq("slug", slug))
      .first(),
});

export const list = query({
  args: {},
  handler: async (ctx) => ctx.db.query("brands").order("desc").take(50),
});
