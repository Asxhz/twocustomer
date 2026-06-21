import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Create-or-return a user by email. role defaults to "customer"; the first user
// of a company is promoted to admin by the login flow (which passes role).
export const upsert = mutation({
  args: {
    email: v.string(),
    role: v.optional(v.string()),
    companyId: v.optional(v.id("companies")),
    name: v.optional(v.string()),
    passwordHash: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", args.email))
      .first();
    if (existing) {
      const patch: Record<string, unknown> = {};
      if (args.role) patch.role = args.role;
      if (args.companyId) patch.companyId = args.companyId;
      if (args.name) patch.name = args.name;
      if (args.passwordHash) patch.passwordHash = args.passwordHash;
      if (Object.keys(patch).length) await ctx.db.patch(existing._id, patch);
      return existing._id;
    }
    return await ctx.db.insert("users", {
      email: args.email,
      role: args.role ?? "customer",
      companyId: args.companyId,
      name: args.name,
      passwordHash: args.passwordHash,
      createdAt: Date.now(),
    });
  },
});

export const getByEmail = query({
  args: { email: v.string() },
  handler: async (ctx, { email }) =>
    ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", email))
      .first(),
});

export const setRole = mutation({
  args: { email: v.string(), role: v.string() },
  handler: async (ctx, { email, role }) => {
    const u = await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", email))
      .first();
    if (u) await ctx.db.patch(u._id, { role });
    return u?._id ?? null;
  },
});
