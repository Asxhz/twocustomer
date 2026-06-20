import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

// Proxy an agent-generated image asset so the browser can load it.
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  try {
    const r = await fetch(`${AGENT_BASE_URL}/assets/${id}`, { headers: agentHeaders() });
    if (!r.ok) return new Response("not found", { status: 404 });
    return new Response(r.body, {
      headers: { "Content-Type": r.headers.get("content-type") || "image/png" },
    });
  } catch {
    return new Response("agent unreachable", { status: 502 });
  }
}
