import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";
import { getSession } from "@/lib/session";
import { convexQuery } from "@/lib/convexApi";
import { decryptSecret } from "@/lib/crypto";

export const maxDuration = 300;

interface CompanyRow {
  githubTokenEnc?: string;
}

// Proxy a GitHub-repo FDE request to the agent: read → diagnose → patch → PR.
// Forwards the company's connected OAuth token so the PR is opened under their
// account (admin only. customers are gated out by the proxy + agent roles).
export async function POST(req: Request) {
  const session = await getSession();
  if (!session || session.role !== "admin") {
    return Response.json({ error: "Admins only." }, { status: 403 });
  }
  const incoming = await req.json().catch(() => ({}));

  // Attach the company's GitHub token if connected.
  if (session.companyId && !incoming.github_token) {
    const company = await convexQuery<CompanyRow | null>("companies:get", {
      id: session.companyId,
    });
    if (company?.githubTokenEnc) {
      const tok = await decryptSecret(company.githubTokenEnc);
      if (tok) incoming.github_token = tok;
    }
  }

  try {
    const r = await fetch(`${AGENT_BASE_URL}/fde/github`, {
      method: "POST",
      headers: agentHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(incoming),
    });
    return Response.json(await r.json());
  } catch {
    return Response.json({ error: "Agent unreachable." });
  }
}
