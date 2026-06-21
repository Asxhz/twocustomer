import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

export const maxDuration = 60;

// Text -> speech (Deepgram) so the agent talks back. Returns audio/mpeg.
export async function POST(req: Request) {
  const { text } = await req.json().catch(() => ({ text: "" }));
  if (!text) return new Response("", { status: 400 });
  try {
    const upstream = await fetch(`${AGENT_BASE_URL}/voice/speak`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ message: text }),
    });
    if (!upstream.ok || !upstream.body) return new Response("", { status: 502 });
    return new Response(upstream.body, {
      headers: { "Content-Type": "audio/mpeg", "Cache-Control": "no-store" },
    });
  } catch {
    return new Response("", { status: 502 });
  }
}
