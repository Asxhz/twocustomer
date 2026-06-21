import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { convexMutation } from "@/lib/convexApi";
import { encryptSecret } from "@/lib/crypto";

// Connect GitHub by pasting a Personal Access Token (the "as a dev" path. no
// OAuth app needed). We verify the token, store it encrypted on the company,
// and the FDE then opens PRs under that identity. Admin only.
export async function POST(req: Request) {
  const session = await getSession();
  if (!session?.companyId || session.role !== "admin") {
    return NextResponse.json({ ok: false, error: "Admins only." }, { status: 403 });
  }
  const { token } = await req.json().catch(() => ({}));
  const pat = (token || "").toString().trim();
  if (!pat) return NextResponse.json({ ok: false, error: "Paste a token." }, { status: 400 });

  // Verify it + grab the login.
  let login = "token";
  try {
    const r = await fetch("https://api.github.com/user", {
      headers: { Authorization: `Bearer ${pat}`, "User-Agent": "twocustomer" },
    });
    if (!r.ok) {
      return NextResponse.json(
        { ok: false, error: "Token rejected by GitHub. check it has repo scope." },
        { status: 400 },
      );
    }
    const u = await r.json();
    login = u.login ?? "token";
  } catch {
    return NextResponse.json({ ok: false, error: "Couldn't reach GitHub." }, { status: 502 });
  }

  await convexMutation("companies:setGithub", {
    id: session.companyId,
    githubLogin: login,
    githubTokenEnc: await encryptSecret(pat),
  });
  return NextResponse.json({ ok: true, login });
}
