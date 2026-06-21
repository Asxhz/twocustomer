import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

// Preview/PR links the voice agent produced during a call. The call UI polls
// this so the link always shows in a fixed panel, not just the Daily chat.
export async function GET(req: Request) {
  const room = new URL(req.url).searchParams.get("room") || "";
  try {
    const r = await fetch(
      `${AGENT_BASE_URL}/call/links?room=${encodeURIComponent(room)}`,
      { headers: agentHeaders(), cache: "no-store" },
    );
    return Response.json(await r.json());
  } catch {
    return Response.json({ room, links: [] });
  }
}
