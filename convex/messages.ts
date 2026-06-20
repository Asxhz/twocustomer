import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const append = mutation({
  args: {
    participant: v.string(),
    role: v.string(),
    content: v.string(),
    channel: v.optional(v.string()),
  },
  handler: async (ctx, args) =>
    ctx.db.insert("messages", { ...args, ts: Date.now() }),
});

export const list = query({
  args: { participant: v.string(), limit: v.optional(v.number()) },
  handler: async (ctx, { participant, limit }) =>
    ctx.db
      .query("messages")
      .withIndex("by_participant", (q) => q.eq("participant", participant))
      .order("desc")
      .take(limit ?? 30),
});
