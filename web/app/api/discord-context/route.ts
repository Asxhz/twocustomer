import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

// Pull recent team messages from the brand's Discord channel (agent context).
export async function GET() {
  try {
    const r = await fetch(`${AGENT_BASE_URL}/discord/context`, {
      headers: agentHeaders(),
      cache: "no-store",
    });
    return Response.json(await r.json());
  } catch {
    return Response.json({ context: "", configured: false });
  }
}
