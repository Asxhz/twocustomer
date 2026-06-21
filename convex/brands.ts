import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Create-or-return a brand by slug (idempotent seed).
export const upsert = mutation({
  args: {
    name: v.string(),
    slug: v.string(),
    companyId: v.optional(v.id("companies")),
    terms: v.array(v.string()),
    handles: v.optional(
      v.object({
        x: v.optional(v.string()),
        reddit: v.optional(v.string()),
        linkedin: v.optional(v.string()),
      }),
    ),
    type: v.optional(v.string()), // "software" | "physical"
    repoUrl: v.optional(v.string()),
    discordChannel: v.optional(v.string()),
    ownerEmail: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("brands")
      .withIndex("by_slug", (q) => q.eq("slug", args.slug))
      .first();
    if (existing) {
      // update project metadata on re-connect
      const { slug: _s, ...rest } = args;
      await ctx.db.patch(existing._id, rest);
      return existing._id;
    }
    return await ctx.db.insert("brands", { ...args, createdAt: Date.now() });
  },
});

// Projects owned by an email (the picker), newest first. Falls back to all when
// no email given (demo).
export const listByOwner = query({
  args: { ownerEmail: v.optional(v.string()) },
  handler: async (ctx, { ownerEmail }) => {
    const all = await ctx.db.query("brands").order("desc").take(100);
    if (!ownerEmail) return all.slice(0, 50);
    const mine = all.filter((b) => b.ownerEmail === ownerEmail);
    // include seeded demos (no owner) so a new user always sees examples
    const demos = all.filter((b) => !b.ownerEmail).slice(0, 4);
    return [...mine, ...demos].slice(0, 50);
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
