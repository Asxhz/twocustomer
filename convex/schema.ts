import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

// TwoCustomer realtime state. Brands own everything; mentions/insights/campaigns/
// packets hang off a brand. messages = chat transcript per participant.
export default defineSchema({
  // A company is the top-level tenant the admin sets up first. Brands hang off it.
  companies: defineTable({
    name: v.string(),
    ownerEmail: v.string(),
    githubOrg: v.optional(v.string()),
    githubLogin: v.optional(v.string()),   // connected GitHub account
    githubTokenEnc: v.optional(v.string()), // encrypted OAuth token
    discordGuild: v.optional(v.string()),
    discordGuildId: v.optional(v.string()), // linked Discord server id (/setup)
    discordTokenEnc: v.optional(v.string()), // encrypted Discord OAuth token
    setupComplete: v.optional(v.boolean()), // gates the app until first-run wizard done
    createdAt: v.number(),
  }).index("by_owner", ["ownerEmail"]).index("by_guild", ["discordGuildId"]),

  // People who can sign in. role gates the surface (admin console vs customer /u).
  users: defineTable({
    email: v.string(),
    role: v.string(),                       // "admin" | "customer"
    companyId: v.optional(v.id("companies")),
    name: v.optional(v.string()),
    passwordHash: v.optional(v.string()),   // pbkdf2$... (admins); customers may be guests
    createdAt: v.number(),
  }).index("by_email", ["email"]),

  // Concrete things a brand sells / ships — the unit the FDE/CMO operate on.
  products: defineTable({
    brandId: v.id("brands"),
    name: v.string(),
    kind: v.string(),                       // "software" | "physical"
    repoUrl: v.optional(v.string()),
    assetUrl: v.optional(v.string()),
    description: v.optional(v.string()),
    createdAt: v.number(),
  }).index("by_brand", ["brandId"]),

  // In-dashboard notifications (replaces email): alerts, new insight, PR opened, etc.
  notifications: defineTable({
    companyId: v.optional(v.id("companies")),
    brandId: v.optional(v.id("brands")),
    kind: v.string(),                       // alert | insight | campaign | fix | interview
    title: v.string(),
    body: v.optional(v.string()),
    href: v.optional(v.string()),
    read: v.boolean(),
    ts: v.number(),
  })
    .index("by_company", ["companyId"])
    .index("by_brand", ["brandId"]),

  // Discord invite tracking: who was invited, to which brand, signed up yet.
  invites: defineTable({
    discordUserId: v.optional(v.string()),
    brand: v.optional(v.string()),
    email: v.optional(v.string()),
    used: v.optional(v.boolean()),
    createdAt: v.number(),
  }),

  // Customer reward ledger (loyalty for completing interviews / referrals).
  rewards: defineTable({
    brandId: v.id("brands"),
    customer: v.string(),                   // customer email
    label: v.string(),
    points: v.number(),
    status: v.string(),                     // earned | available | redeemable | redeemed
    createdAt: v.number(),
  })
    .index("by_brand", ["brandId"])
    .index("by_customer", ["customer"]),

  brands: defineTable({
    name: v.string(),
    slug: v.string(),
    companyId: v.optional(v.id("companies")),
    terms: v.array(v.string()), // brand search terms
    handles: v.optional(v.object({
      x: v.optional(v.string()),
      reddit: v.optional(v.string()),
      linkedin: v.optional(v.string()),
    })),
    type: v.optional(v.string()),          // "software" | "physical"
    repoUrl: v.optional(v.string()),
    discordChannel: v.optional(v.string()),
    ownerEmail: v.optional(v.string()),    // who owns this project
    createdAt: v.number(),
  }).index("by_slug", ["slug"]).index("by_company", ["companyId"]),

  mentions: defineTable({
    brandId: v.id("brands"),
    platform: v.string(), // x | reddit | linkedin | web
    externalId: v.string(), // dedup key
    author: v.optional(v.string()),
    text: v.string(),
    url: v.optional(v.string()),
    score: v.number(),
    highSignal: v.boolean(),
    ts: v.number(),
  })
    .index("by_brand", ["brandId"])
    .index("by_brand_external", ["brandId", "externalId"]),

  insights: defineTable({
    brandId: v.id("brands"),
    title: v.string(),
    body: v.string(),
    severity: v.optional(v.string()), // info | opportunity | risk
    sourceMentionIds: v.optional(v.array(v.id("mentions"))),
    createdAt: v.number(),
  }).index("by_brand", ["brandId"]),

  campaigns: defineTable({
    brandId: v.id("brands"),
    brief: v.string(),
    body: v.string(),
    status: v.string(), // draft | ready
    createdAt: v.number(),
  }).index("by_brand", ["brandId"]),

  packets: defineTable({
    brandId: v.id("brands"),
    title: v.string(),
    summary: v.string(),
    evidence: v.optional(v.array(v.string())),
    recommendedAction: v.optional(v.string()),
    artifact: v.optional(v.string()), // diff / plan
    createdAt: v.number(),
  }).index("by_brand", ["brandId"]),

  sessions: defineTable({
    brandId: v.id("brands"),
    customer: v.string(),
    channel: v.string(), // voice | web | slack
    transcript: v.array(v.object({ role: v.string(), text: v.string() })),
    insightId: v.optional(v.id("insights")),
    status: v.string(),
    createdAt: v.number(),
  }).index("by_brand", ["brandId"]),

  messages: defineTable({
    participant: v.string(),
    role: v.string(), // user | assistant
    content: v.string(),
    channel: v.optional(v.string()),
    ts: v.number(),
  }).index("by_participant", ["participant"]),

  memory_index: defineTable({
    brandId: v.id("brands"),
    kind: v.string(), // insight | campaign
    refId: v.string(),
    text: v.string(),
    createdAt: v.number(),
  }).index("by_brand", ["brandId"]),
});
