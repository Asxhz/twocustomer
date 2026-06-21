import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";
import { getSession } from "@/lib/session";

export const maxDuration = 300;

// Run a real signal search for a project. Admin only.
export async function POST(req: Request) {
  const session = await getSession();
  if (!session || session.role !== "admin") {
    return Response.json({ error: "Admins only." }, { status: 403 });
  }
  const body = await req.json().catch(() => ({}));
  if (!body.brand_slug) return Response.json({ error: "No project selected." });
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 120_000);
    const r = await fetch(`${AGENT_BASE_URL}/research`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    clearTimeout(t);
    try {
      return Response.json(await r.json());
    } catch {
      return Response.json({ error: "Agent returned an unexpected response." });
    }
  } catch {
    return Response.json({ error: "Agent unreachable. Check the agent deployment." });
  }
}
