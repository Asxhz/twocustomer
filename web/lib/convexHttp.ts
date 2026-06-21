// Server-side Convex access over the HTTP API. REAL data only.
//
// There is no mock and no DEMO_MODE. Every accessor returns live rows or an
// empty result with an honest `source` ("live" | "empty" | "unavailable").
// The UI renders real data or a clear empty/offline state, never fake rows.

import { convexQuery as cq, convexConfigured } from "./convexApi";

export type DataSource = "live" | "empty" | "unavailable";

export interface Loaded<T> {
  rows: T[];
  source: DataSource;
  live: boolean;
}

export interface MentionRow {
  platform: string;
  author?: string;
  text: string;
  url?: string;
  score: number;
  highSignal: boolean;
}

function pack<T>(rows: T[], source: DataSource): Loaded<T> {
  return { rows, source, live: source === "live" };
}

async function selectedSlug(): Promise<string> {
  try {
    const { cookies } = await import("next/headers");
    return (await cookies()).get("tc_project")?.value || "";
  } catch {
    return "";
  }
}

export async function resolveBrandId(): Promise<string | null> {
  const slug = await selectedSlug();
  if (!slug) return null;
  const brand = await cq<{ _id?: string } | null>("brands:getBySlug", { slug });
  return brand?._id ?? null;
}

export async function activeBrandName(): Promise<string> {
  const slug = await selectedSlug();
  if (!convexConfigured || !slug) return "our team";
  const brand = await cq<{ name?: string } | null>("brands:getBySlug", { slug });
  return brand?.name || "our team";
}

// Resolve brand then run a brand-scoped list query. Never fabricates rows.
async function liveOrEmpty<T>(path: string): Promise<Loaded<T>> {
  if (!convexConfigured) return pack<T>([], "unavailable");
  const brandId = await resolveBrandId();
  if (!brandId) return pack<T>([], "empty");
  const rows = await cq<T[]>(path, { brandId, limit: 50 });
  if (rows === null) return pack<T>([], "unavailable");
  return pack<T>(rows, rows.length ? "live" : "empty");
}

export interface InsightRow { _id?: string; title: string; body: string; severity?: string }
export interface CampaignRow { _id?: string; brief: string; body: string; status: string }
export interface PacketRow { _id?: string; title: string; summary: string; evidence?: string[]; recommendedAction?: string; artifact?: string }
export interface SessionRow { _id?: string; customer: string; channel: string; status: string; transcript?: { role: string; text: string }[] }
export interface RewardRow { _id?: string; label: string; points: number; status: string }

export const listMentions = () => liveOrEmpty<MentionRow>("mentions:listMentions");
export const listInsights = () => liveOrEmpty<InsightRow>("insights:listInsights");
export const listCampaigns = () => liveOrEmpty<CampaignRow>("campaigns:list");
export const listPackets = () => liveOrEmpty<PacketRow>("packets:list");
export const listSessions = () => liveOrEmpty<SessionRow>("sessions:list");

export async function getSessionById(id: string) {
  if (!convexConfigured) return null;
  return cq<unknown>("sessions:get", { id });
}
export async function getPacketById(id: string) {
  if (!convexConfigured) return null;
  return cq<unknown>("packets:get", { id });
}

export async function listRewardsByCustomer(customer: string): Promise<Loaded<RewardRow>> {
  if (!convexConfigured) return pack<RewardRow>([], "unavailable");
  const rows = await cq<RewardRow[]>("rewards:listByCustomer", { customer });
  if (rows === null) return pack<RewardRow>([], "unavailable");
  return pack<RewardRow>(rows, rows.length ? "live" : "empty");
}

export interface AnalyticsSummary {
  totals: { mentions: number; highSignal: number; insights: number; campaigns: number; packets: number; sessions: number };
  byPlatform: Record<string, number>;
  bySeverity: Record<string, number>;
  campaignStatus: Record<string, number>;
  timeline: { day: string; count: number; avgScore: number; highSignal: number }[];
}

export async function analyticsSummary(): Promise<{ data: AnalyticsSummary | null; source: DataSource }> {
  if (!convexConfigured) return { data: null, source: "unavailable" };
  const brandId = await resolveBrandId();
  if (!brandId) return { data: null, source: "empty" };
  const data = await cq<AnalyticsSummary>("analytics:summary", { brandId });
  if (!data) return { data: null, source: "unavailable" };
  const empty = data.totals.mentions + data.totals.insights + data.totals.sessions === 0;
  return { data, source: empty ? "empty" : "live" };
}

export async function graphForBrand(): Promise<{
  nodes: { id: string; type: string; label: string; meta?: string }[];
  edges: { id: string; source: string; target: string }[];
  source: DataSource;
}> {
  if (!convexConfigured) return { nodes: [], edges: [], source: "unavailable" };
  const brandId = await resolveBrandId();
  if (!brandId) return { nodes: [], edges: [], source: "empty" };
  const g = await cq<{ nodes: never[]; edges: never[] }>("graph:forBrand", { brandId });
  if (!g) return { nodes: [], edges: [], source: "unavailable" };
  return { ...g, source: g.nodes.length ? "live" : "empty" };
}
