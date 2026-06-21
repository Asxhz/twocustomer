import { mutation } from "./_generated/server";

// Danger: deletes ALL rows from every table. Used once to clear seeded/demo data
// so the app starts truly empty and real. Re-run only intentionally.
export const wipeAll = mutation({
  args: {},
  handler: async (ctx) => {
    const tables = [
      "companies", "users", "brands", "products", "mentions", "insights",
      "campaigns", "packets", "sessions", "messages", "rewards",
      "notifications", "memory_index",
    ] as const;
    let n = 0;
    for (const t of tables) {
      const docs = await ctx.db.query(t).collect();
      for (const d of docs) {
        await ctx.db.delete(d._id);
        n++;
      }
    }
    return n;
  },
});
