import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// The invite token IS the doc id (unique, unguessable enough for this flow).
export const create = mutation({
  args: { discordUserId: v.optional(v.string()), brand: v.optional(v.string()) },
  handler: async (ctx, args) => {
    const id = await ctx.db.insert("invites", {
      discordUserId: args.discordUserId,
      brand: args.brand,
      used: false,
      createdAt: Date.now(),
    });
    return id;
  },
});

export const get = query({
  args: { id: v.id("invites") },
  handler: async (ctx, { id }) => ctx.db.get(id),
});

export const markUsed = mutation({
  args: { id: v.id("invites"), email: v.optional(v.string()) },
  handler: async (ctx, { id, email }) => {
    await ctx.db.patch(id, { used: true, email });
    return id;
  },
});
