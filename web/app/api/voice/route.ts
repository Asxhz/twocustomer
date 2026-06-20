import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

// Proxy recorded audio to the agent's Deepgram STT endpoint, return transcript.
export async function POST(req: Request) {
  const audio = await req.arrayBuffer();
  const contentType = req.headers.get("content-type") || "audio/webm";
  try {
    const upstream = await fetch(`${AGENT_BASE_URL}/voice/transcribe`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": contentType }),
      body: audio,
    });
    if (!upstream.ok) {
      return Response.json({ transcript: "", error: `agent ${upstream.status}` });
    }
    return Response.json(await upstream.json());
  } catch (e) {
    return Response.json({ transcript: "", error: String(e) });
  }
}
