import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";
import { getSession } from "@/lib/session";
import { convexQuery } from "@/lib/convexApi";
import { decryptSecret } from "@/lib/crypto";

export const maxDuration = 300;

interface CompanyRow {
  githubTokenEnc?: string;
}

// Connected-repo FDE: read → diagnose → patch → PR + live preview. Forwards the
// company's GitHub OAuth token. Admin only.
export async function POST(req: Request) {
  const session = await getSession();
  if (!session || session.role !== "admin") {
    return Response.json({ error: "Admins only." }, { status: 403 });
  }
  const incoming = await req.json().catch(() => ({}));
  // repo_url may be empty — the agent falls back to the hardcoded demo repo.
  if (session.companyId && !incoming.github_token) {
    const company = await convexQuery<CompanyRow | null>("companies:get", { id: session.companyId });
    if (company?.githubTokenEnc) {
      const tok = await decryptSecret(company.githubTokenEnc);
      if (tok) incoming.github_token = tok;
    }
  }
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 290_000);
    const r = await fetch(`${AGENT_BASE_URL}/fde/repo`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(incoming),
      signal: ctrl.signal,
    });
    clearTimeout(t);
    return Response.json(await r.json());
  } catch {
    return Response.json({ error: "Agent unreachable. check the agent deployment." });
  }
}
