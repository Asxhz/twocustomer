import { cookies } from "next/headers";
import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

export const maxDuration = 60;

// Start a live call: the agent creates a Daily room and sends the voice agent in.
// brand_slug (from the selected project cookie) picks which repo the agent can fix.
export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  if (!body.brand_slug) {
    const slug = (await cookies()).get("tc_project")?.value;
    if (slug) body.brand_slug = slug;
  }
  try {
    const r = await fetch(`${AGENT_BASE_URL}/call/start`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ brand_slug: body.brand_slug || "" }),
    });
    return Response.json(await r.json());
  } catch {
    return Response.json({ error: "Agent unreachable.", room_url: null });
  }
}
