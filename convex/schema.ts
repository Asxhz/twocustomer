import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

// TwoCustomer realtime state. Brands own everything; mentions/insights/campaigns/
// packets hang off a brand. messages = chat transcript per participant.
export default defineSchema({
  brands: defineTable({
    name: v.string(),
    slug: v.string(),
    terms: v.array(v.string()), // brand search terms
    handles: v.optional(v.object({
      x: v.optional(v.string()),
      reddit: v.optional(v.string()),
      linkedin: v.optional(v.string()),
    })),
    createdAt: v.number(),
  }).index("by_slug", ["slug"]),

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
