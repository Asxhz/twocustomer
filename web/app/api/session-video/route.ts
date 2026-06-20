import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

// Ask the agent to create a Daily room (video + screen share) and return it.
export async function POST() {
  try {
    const r = await fetch(`${AGENT_BASE_URL}/session/video`, { method: "POST", headers: agentHeaders() });
    return Response.json(await r.json());
  } catch {
    return Response.json({ room_url: null, error: "agent unreachable" });
  }
}
