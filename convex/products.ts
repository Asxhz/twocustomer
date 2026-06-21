import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Products are the things a brand sells/ships — what the FDE/CMO operate on.
export const add = mutation({
  args: {
    brandId: v.string(), // slug
    name: v.string(),
    kind: v.string(), // software | physical
    repoUrl: v.optional(v.string()),
    assetUrl: v.optional(v.string()),
    description: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { brandId, ...rest } = args;
    const brand = await ctx.db
      .query("brands")
      .withIndex("by_slug", (q) => q.eq("slug", brandId))
      .first();
    if (!brand) return null;
    return ctx.db.insert("products", {
      brandId: brand._id,
      ...rest,
      createdAt: Date.now(),
    });
  },
});

export const listByBrand = query({
  args: { brandId: v.id("brands") },
  handler: async (ctx, { brandId }) =>
    ctx.db
      .query("products")
      .withIndex("by_brand", (q) => q.eq("brandId", brandId))
      .order("desc")
      .take(50),
});
