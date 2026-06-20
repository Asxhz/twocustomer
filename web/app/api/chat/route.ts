import { cookies } from "next/headers";
import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

// Agent tool loops can run well past Vercel's default function limit.
export const maxDuration = 300;

// Proxy the browser's chat request to the agent control plane and stream the
// agent's SSE response straight back. Keeps the agent URL/token server-side.
function sseError(msg: string): Response {
  // Return a well-formed SSE stream so the client renders the error inline
  // instead of seeing a dead 500.
  const body =
    `event: error\ndata: ${JSON.stringify({ error: msg })}\n\n` +
    `event: done\ndata: {}\n\n`;
  return new Response(body, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
  });
}

export async function POST(req: Request) {
  const raw = await req.json().catch(() => ({}));
  // Inject the selected project so the agent is project-aware.
  const slug = (await cookies()).get("tc_project")?.value;
  if (slug && !raw.brand_slug) raw.brand_slug = slug;
  const body = JSON.stringify(raw);
  let upstream: Response;
  try {
    upstream = await fetch(`${AGENT_BASE_URL}/chat`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": "application/json" }),
      body,
    });
  } catch {
    return sseError("Agent unreachable — is the control plane running on :8000?");
  }

  if (!upstream.ok || !upstream.body) {
    return sseError(`Agent returned ${upstream.status}.`);
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
