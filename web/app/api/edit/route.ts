import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

export const maxDuration = 300;

export async function POST(req: Request) {
  const body = await req.text();
  try {
    const r = await fetch(`${AGENT_BASE_URL}/edit/image`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": "application/json" }),
      body,
    });
    const data = await r.json();
    // rewrite the agent-served asset path to a browser-reachable proxy
    if (data.url?.startsWith("/assets/")) {
      data.url = "/api/asset/" + data.url.slice("/assets/".length);
    }
    return Response.json(data);
  } catch {
    return Response.json({ message: "agent unreachable", url: null });
  }
}
