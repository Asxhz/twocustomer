import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Customer loyalty ledger. brandId arrives as a slug from the agent/seed.
export const add = mutation({
  args: {
    brandId: v.string(),
    customer: v.string(),
    label: v.string(),
    points: v.number(),
    status: v.string(),
  },
  handler: async (ctx, args) => {
    const { brandId, ...rest } = args;
    const brand = await ctx.db
      .query("brands")
      .withIndex("by_slug", (q) => q.eq("slug", brandId))
      .first();
    if (!brand) return null;
    return ctx.db.insert("rewards", {
      brandId: brand._id,
      ...rest,
      createdAt: Date.now(),
    });
  },
});

export const listByBrand = query({
  args: { brandId: v.id("brands"), limit: v.optional(v.number()) },
  handler: async (ctx, { brandId, limit }) =>
    ctx.db
      .query("rewards")
      .withIndex("by_brand", (q) => q.eq("brandId", brandId))
      .order("desc")
      .take(limit ?? 50),
});

export const listByCustomer = query({
  args: { customer: v.string(), limit: v.optional(v.number()) },
  handler: async (ctx, { customer, limit }) =>
    ctx.db
      .query("rewards")
      .withIndex("by_customer", (q) => q.eq("customer", customer))
      .order("desc")
      .take(limit ?? 50),
});
