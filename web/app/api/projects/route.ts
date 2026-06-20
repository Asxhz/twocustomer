import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

const CONVEX_URL = (process.env.CONVEX_URL || "").replace(/\/$/, "");

async function convex(kind: "query" | "mutation", path: string, args: Record<string, unknown>) {
  if (!CONVEX_URL) return null;
  const r = await fetch(`${CONVEX_URL}/api/${kind}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, args, format: "json" }),
    cache: "no-store",
  });
  const b = await r.json().catch(() => ({}));
  return b.status === "success" ? b.value : null;
}

function slugify(s: string) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

// GET — the signed-in user's projects (+ seeded demos).
export async function GET() {
  const email = (await cookies()).get("tc_user")?.value ?? null;
  const selected = (await cookies()).get("tc_project")?.value ?? null;
  const rows = (await convex("query", "brands:listByOwner", { ownerEmail: email ?? undefined })) || [];
  return NextResponse.json({ projects: rows, selected });
}

// POST — create/connect a project, persist it, arm monitors, and select it.
export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const name = (body.name ?? "").toString().trim();
  if (!name) return NextResponse.json({ error: "name required" }, { status: 400 });
  const slug = slugify(name);
  const email = (await cookies()).get("tc_user")?.value ?? "";
  const type = body.type === "software" ? "software" : "physical";
  const repoUrl = (body.repoUrl ?? "").toString().trim();
  const discordChannel = (body.discordChannel ?? "").toString().trim();
  const terms = Array.isArray(body.terms)
    ? body.terms
    : (body.terms ?? "").toString().split(",").map((t: string) => t.trim()).filter(Boolean);
  if (!terms.length) terms.push(name);

  // 1) persist the project in Convex
  await convex("mutation", "brands:upsert", {
    name, slug, terms, type, repoUrl, discordChannel, ownerEmail: email,
  });

  // 2) arm the agent's monitor + store project metadata
  try {
    await fetch(`${AGENT_BASE_URL}/monitor/config`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        brand_slug: slug, name, terms, enabled: true,
        project_type: type, repo_url: repoUrl, discord_channel: discordChannel,
      }),
    });
  } catch {
    /* agent optional at create time */
  }

  // 3) select it (cache)
  const res = NextResponse.json({ ok: true, slug });
  res.cookies.set("tc_project", slug, { httpOnly: false, sameSite: "lax", path: "/", maxAge: 60 * 60 * 24 * 30 });
  return res;
}
