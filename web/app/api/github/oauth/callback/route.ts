import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getSession } from "@/lib/session";
import { convexMutation } from "@/lib/convexApi";
import { encryptSecret } from "@/lib/crypto";

// GitHub redirects here with ?code&state. Exchange the code, store the token
// encrypted on the company, then return to setup.
export async function GET(req: Request) {
  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const cookieState = (await cookies()).get("gh_oauth_state")?.value;
  const session = await getSession();

  const back = (q: string) => NextResponse.redirect(new URL(`/admin/setup?github=${q}`, req.url));

  if (!session?.companyId) return NextResponse.redirect(new URL("/sign-in", req.url));
  if (!code || !state || state !== cookieState) return back("error");

  const clientId = process.env.GITHUB_CLIENT_ID;
  const clientSecret = process.env.GITHUB_CLIENT_SECRET;
  if (!clientId || !clientSecret) return back("unconfigured");

  try {
    const tokenRes = await fetch("https://github.com/login/oauth/access_token", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ client_id: clientId, client_secret: clientSecret, code }),
    });
    const tokenBody = await tokenRes.json();
    const accessToken: string | undefined = tokenBody.access_token;
    if (!accessToken) return back("error");

    const userRes = await fetch("https://api.github.com/user", {
      headers: { Authorization: `Bearer ${accessToken}`, "User-Agent": "twocustomer" },
    });
    const user = await userRes.json();

    await convexMutation("companies:setGithub", {
      id: session.companyId,
      githubLogin: user.login ?? "unknown",
      githubTokenEnc: await encryptSecret(accessToken),
    });
    return back("connected");
  } catch {
    return back("error");
  }
}
