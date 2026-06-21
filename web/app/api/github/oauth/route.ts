import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";

// Start the GitHub OAuth dance. Register an OAuth App and set GITHUB_CLIENT_ID /
// GITHUB_CLIENT_SECRET; callback must be <web>/api/github/oauth/callback.
export async function GET(req: Request) {
  const session = await getSession();
  if (!session || session.role !== "admin") {
    return NextResponse.redirect(new URL("/sign-in", req.url));
  }
  const clientId = process.env.GITHUB_CLIENT_ID;
  if (!clientId) {
    // No creds yet. bounce back to setup with a flag the UI can explain.
    return NextResponse.redirect(new URL("/admin/setup?github=unconfigured", req.url));
  }
  const origin = process.env.WEB_BASE_URL || new URL(req.url).origin;
  const redirectUri = `${origin}/api/github/oauth/callback`;
  const state = crypto.randomUUID();

  const url = new URL("https://github.com/login/oauth/authorize");
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("scope", "repo read:org");
  url.searchParams.set("state", state);

  const res = NextResponse.redirect(url);
  res.cookies.set("gh_oauth_state", state, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 600,
  });
  return res;
}
