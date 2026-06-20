import { NextResponse } from "next/server";
import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

export const maxDuration = 300;

// Persist a brand's monitor config to the agent control plane (which writes it
// to Redis and arms the scheduler). Called from onboarding "Arm monitors".
export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const brand = (body.brand ?? "").toString().trim();
  if (!brand) {
    return NextResponse.json({ error: "brand required" }, { status: 400 });
  }
  const slug = brand
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
  const terms = Array.isArray(body.terms)
    ? body.terms
    : (body.terms ?? "")
        .toString()
        .split(",")
        .map((t: string) => t.trim())
        .filter(Boolean);
  // Always seed the brand name itself as a term.
  if (!terms.length) terms.push(brand);

  try {
    const r = await fetch(`${AGENT_BASE_URL}/monitor/config`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ brand_slug: slug, terms, enabled: true }),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      return NextResponse.json(
        { error: data?.detail ?? "agent error", slug },
        { status: r.status },
      );
    }
    return NextResponse.json({ ok: true, slug, config: data.config });
  } catch (e) {
    return NextResponse.json(
      { error: `agent unreachable: ${(e as Error).message}`, slug },
      { status: 502 },
    );
  }
}
