import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// One company per founder (keyed by ownerEmail). Created on first admin sign-in
// or by the setup wizard; setupComplete gates the rest of the app.
export const upsert = mutation({
  args: {
    name: v.string(),
    ownerEmail: v.string(),
    githubOrg: v.optional(v.string()),
    discordGuild: v.optional(v.string()),
    setupComplete: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("companies")
      .withIndex("by_owner", (q) => q.eq("ownerEmail", args.ownerEmail))
      .first();
    if (existing) {
      const { ownerEmail: _o, ...rest } = args;
      await ctx.db.patch(existing._id, rest);
      return existing._id;
    }
    return await ctx.db.insert("companies", { ...args, createdAt: Date.now() });
  },
});

export const getByOwner = query({
  args: { ownerEmail: v.string() },
  handler: async (ctx, { ownerEmail }) =>
    ctx.db
      .query("companies")
      .withIndex("by_owner", (q) => q.eq("ownerEmail", ownerEmail))
      .first(),
});

export const get = query({
  args: { id: v.id("companies") },
  handler: async (ctx, { id }) => ctx.db.get(id),
});

// Store the connected Discord identity + (encrypted) token after OAuth.
export const setDiscord = mutation({
  args: {
    id: v.id("companies"),
    discordGuild: v.optional(v.string()),
    discordTokenEnc: v.optional(v.string()),
  },
  handler: async (ctx, { id, ...rest }) => {
    const patch = Object.fromEntries(
      Object.entries(rest).filter(([, v]) => v !== undefined),
    );
    if (Object.keys(patch).length) await ctx.db.patch(id, patch);
    return id;
  },
});

// Store the connected GitHub identity + (encrypted) token after OAuth.
export const setGithub = mutation({
  args: {
    id: v.id("companies"),
    githubLogin: v.string(),
    githubTokenEnc: v.string(),
    githubOrg: v.optional(v.string()),
  },
  handler: async (ctx, { id, ...rest }) => {
    await ctx.db.patch(id, rest);
    return id;
  },
});

// Patch arbitrary profile fields by id (used by the setup wizard).
export const update = mutation({
  args: {
    id: v.id("companies"),
    name: v.optional(v.string()),
    discordGuild: v.optional(v.string()),
    githubOrg: v.optional(v.string()),
  },
  handler: async (ctx, { id, ...rest }) => {
    const patch = Object.fromEntries(
      Object.entries(rest).filter(([, v]) => v !== undefined),
    );
    if (Object.keys(patch).length) await ctx.db.patch(id, patch);
    return id;
  },
});

// Link a Discord server to this company (run by /setup, guild-admin only).
export const linkGuild = mutation({
  args: { id: v.id("companies"), guildId: v.string(), guildName: v.optional(v.string()) },
  handler: async (ctx, { id, guildId, guildName }) => {
    await ctx.db.patch(id, { discordGuildId: guildId, discordGuild: guildName });
    return id;
  },
});

// Resolve the company that owns a Discord guild (for /report etc.).
export const getByGuildId = query({
  args: { guildId: v.string() },
  handler: async (ctx, { guildId }) =>
    ctx.db
      .query("companies")
      .withIndex("by_guild", (q) => q.eq("discordGuildId", guildId))
      .first(),
});

export const markSetupComplete = mutation({
  args: { id: v.id("companies") },
  handler: async (ctx, { id }) => {
    await ctx.db.patch(id, { setupComplete: true });
    return id;
  },
});
