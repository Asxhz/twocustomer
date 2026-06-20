// Server-side Convex access over the HTTP API (no React/codegen needed).
// Falls back to mock data when CONVEX_URL is unset, so the UI always renders.

import { BRAND, INSIGHTS, CAMPAIGNS, PACKETS } from "./mock";

const CONVEX_URL = (process.env.CONVEX_URL || "").replace(/\/$/, "");

export interface MentionRow {
  platform: string;
  author?: string;
  text: string;
  url?: string;
  score: number;
  highSignal: boolean;
}

async function convexQuery<T>(path: string, args: Record<string, unknown>): Promise<T | null> {
  if (!CONVEX_URL) return null;
  try {
    const res = await fetch(`${CONVEX_URL}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path, args, format: "json" }),
      cache: "no-store",
    });
    if (!res.ok) return null;
    const body = await res.json();
    return body.status === "success" ? (body.value as T) : null;
  } catch {
    return null;
  }
}

const MOCK_MENTIONS: MentionRow[] = [
  { platform: "x", author: "@thirsty_sam", text: "Aurora Drinks sold out at my Whole Foods AGAIN.", score: 0.92, highSignal: true },
  { platform: "web", author: "BevReview", text: "Aurora's yuzu flavor is the breakout SKU this quarter.", score: 0.7, highSignal: true },
  { platform: "reddit", author: "u/cpg_nerd", text: "Anyone else notice Aurora's new can design?", score: 0.55, highSignal: false },
];

async function resolveBrandId(): Promise<string | null> {
  const brand = await convexQuery<{ _id?: string } | null>("brands:getBySlug", {
    slug: BRAND.slug,
  });
  return brand?._id ?? null;
}

// Generic: resolve brand → run a brand-scoped list query, else fall back to mock.
async function liveOrMock<T>(
  path: string,
  mock: T[],
): Promise<{ rows: T[]; live: boolean }> {
  const brandId = await resolveBrandId();
  if (brandId) {
    const rows = await convexQuery<T[]>(path, { brandId, limit: 50 });
    if (rows) return { rows, live: true };
  }
  return { rows: mock, live: false };
}

export function listMentions() {
  return liveOrMock<MentionRow>("mentions:listMentions", MOCK_MENTIONS);
}

export function listInsights() {
  return liveOrMock<(typeof INSIGHTS)[number]>("insights:listInsights", INSIGHTS);
}

export function listCampaigns() {
  return liveOrMock<(typeof CAMPAIGNS)[number]>("campaigns:list", CAMPAIGNS);
}

export function listPackets() {
  return liveOrMock<(typeof PACKETS)[number]>("packets:list", PACKETS);
}
