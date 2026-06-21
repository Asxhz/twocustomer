import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

export const maxDuration = 300;

// Drives the "show me → I'll fix it" flow: hits the connected-repo FDE so the
// agent reads the project repo, applies the change (bug / color / content),
// opens-or-updates a PR, and deploys a live Vercel preview. Pass iterate:true
// for a follow-up edit so it stacks on the same branch/PR.
export async function POST(req: Request) {
  let body: Record<string, unknown> = {};
  try {
    body = await req.json();
  } catch {
    body = {};
  }
  try {
    const r = await fetch(`${AGENT_BASE_URL}/fde/repo`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        repo_url: body.repo_url ?? "", // empty -> agent uses the connected demo repo
        symptom: body.symptom ?? "",
        context: body.context ?? "",
        iterate: Boolean(body.iterate),
      }),
    });
    return Response.json(await r.json());
  } catch {
    return Response.json({ error: "agent unreachable", resolved: false });
  }
}
