import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// In-dashboard notifications (replaces email). The agent writes these on monitor
// alerts, new insights, PRs opened, completed interviews, etc.
export const add = mutation({
  args: {
    brandId: v.optional(v.string()), // slug; resolved to company+brand
    companyId: v.optional(v.id("companies")),
    kind: v.string(),
    title: v.string(),
    body: v.optional(v.string()),
    href: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { brandId: slug, ...rest } = args;
    let brandId = undefined as undefined | string;
    let companyId = args.companyId;
    if (slug) {
      const brand = await ctx.db
        .query("brands")
        .withIndex("by_slug", (q) => q.eq("slug", slug))
        .first();
      if (brand) {
        brandId = brand._id;
        if (!companyId) companyId = brand.companyId;
      }
    }
    return ctx.db.insert("notifications", {
      ...rest,
      companyId,
      brandId: brandId as never,
      read: false,
      ts: Date.now(),
    });
  },
});

export const listByCompany = query({
  args: { companyId: v.id("companies"), limit: v.optional(v.number()) },
  handler: async (ctx, { companyId, limit }) =>
    ctx.db
      .query("notifications")
      .withIndex("by_company", (q) => q.eq("companyId", companyId))
      .order("desc")
      .take(limit ?? 50),
});

export const listByBrand = query({
  args: { brandId: v.id("brands"), limit: v.optional(v.number()) },
  handler: async (ctx, { brandId, limit }) =>
    ctx.db
      .query("notifications")
      .withIndex("by_brand", (q) => q.eq("brandId", brandId))
      .order("desc")
      .take(limit ?? 50),
});

export const markRead = mutation({
  args: { id: v.id("notifications") },
  handler: async (ctx, { id }) => {
    await ctx.db.patch(id, { read: true });
    return id;
  },
});

export const markAllRead = mutation({
  args: { companyId: v.id("companies") },
  handler: async (ctx, { companyId }) => {
    const rows = await ctx.db
      .query("notifications")
      .withIndex("by_company", (q) => q.eq("companyId", companyId))
      .collect();
    for (const r of rows) if (!r.read) await ctx.db.patch(r._id, { read: true });
    return rows.length;
  },
});
