// Shared mock data for the demo surface until Convex live queries are wired in.

export const BRAND = { name: "Aurora Drinks", slug: "aurora-drinks" };

export const INSIGHTS = [
  {
    id: "i1",
    title: "Stockouts costing ~10% of revenue",
    severity: "risk",
    body: "Aurora sold out at 3 retail accounts for the 3rd straight week. Reorder + reallocate to fix.",
  },
  {
    id: "i2",
    title: "Yuzu is the breakout SKU",
    severity: "opportunity",
    body: "Web + Reddit chatter shows yuzu outperforming. Shift campaign spend here.",
  },
  {
    id: "i3",
    title: "Email flow change cut performance 34%",
    severity: "risk",
    body: "A single flow edit on 6/12 traced to a 34% drop in click-through. Revert recommended.",
  },
];

export const CAMPAIGNS = [
  { id: "c1", name: "Glide Yuzu Launch", status: "ready", brief: "Push the yuzu SKU with creator UGC." },
  { id: "c2", name: "Summer Sparkling Refresh", status: "draft", brief: "Seasonal repositioning vs. competitors." },
];

export const PACKETS = [
  {
    id: "p1",
    title: "Fix the stockout leak",
    summary: "10% of revenue is leaking from repeated retail stockouts at top accounts.",
    recommendedAction: "Raise reorder point at 3 accounts; reallocate yuzu inventory from DTC.",
    evidence: [
      "@thirsty_sam: 'Aurora sold out at my Whole Foods AGAIN' (3rd week)",
      "BevReview: yuzu is the breakout SKU this quarter",
    ],
    artifact: "PR: bump reorder thresholds in inventory config (accounts WF-3122, WF-8810, SP-204).",
  },
];

export const SESSIONS = [
  {
    id: "s1", customer: "Rosie W. (wholesale)", channel: "voice", status: "complete",
    insight: "Wants larger case packs.",
    transcript: [
      { role: "agent", text: "Thanks for hopping on. What would make reordering easier for you?" },
      { role: "customer", text: "Honestly bigger case packs. 12s sell out before my next order lands." },
      { role: "agent", text: "Got it — so a 24-pack SKU for wholesale. Anything on pricing?" },
      { role: "customer", text: "If the per-unit drops a bit at 24, I'd switch everything over." },
    ],
  },
  {
    id: "s2", customer: "Laura R. (DTC)", channel: "web", status: "complete",
    insight: "Confused by subscription pause UX.",
    transcript: [
      { role: "agent", text: "What's the one thing about your subscription you'd change?" },
      { role: "customer", text: "Pausing is buried. I almost cancelled because I couldn't find it." },
    ],
  },
];

export const REWARDS = [
  { id: "r1", label: "Completed interview", points: 250, status: "earned" },
  { id: "r2", label: "Referred a friend", points: 500, status: "available" },
  { id: "r3", label: "20% off next order", points: 250, status: "redeemable" },
];

export const INTEGRATIONS = [
  { name: "Anthropic Claude", role: "Agent brain (claude-sonnet-4-6)", track: "Best Use of Anthropic" },
  { name: "Browserbase", role: "Web monitoring (Stagehand/CDP)", track: "Best Use of Browserbase" },
  { name: "Fetch AI · ASI:One", role: "Discoverable uAgent that takes action", track: "Best Use of Fetch AI" },
  { name: "Deepgram", role: "Voice STT/TTS for customer interviews", track: "Best Use of Deepgram" },
  { name: "Redis (Upstash)", role: "Agent memory + vector recall + cache", track: "Redis: Beyond Caching" },
  { name: "Discord", role: "Customer-signal intake + alerts + /twocustomer command", track: "—" },
  { name: "Slack", role: "Brand alert channel + slash commands", track: "—" },
  { name: "Convex", role: "Realtime state + live monitor feed", track: "—" },
];
