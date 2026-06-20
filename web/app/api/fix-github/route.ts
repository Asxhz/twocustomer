import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

export const maxDuration = 300;

// Proxy a GitHub-repo FDE request to the agent: clone → diagnose → patch → PR.
export async function POST(req: Request) {
  const body = await req.text();
  try {
    const r = await fetch(`${AGENT_BASE_URL}/fde/github`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": "application/json" }),
      body,
    });
    return Response.json(await r.json());
  } catch {
    return Response.json({ error: "Agent unreachable." });
  }
}
