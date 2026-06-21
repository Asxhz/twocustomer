import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";

// Start Discord OAuth. Set DISCORD_CLIENT_ID / DISCORD_CLIENT_SECRET; callback
// must be <web>/api/discord/oauth/callback. Scope identify+guilds so we can read
// which server the brand wants TwoCustomer to watch.
export async function GET(req: Request) {
  const session = await getSession();
  if (!session || session.role !== "admin") {
    return NextResponse.redirect(new URL("/sign-in", req.url));
  }
  const clientId = process.env.DISCORD_CLIENT_ID;
  if (!clientId) {
    return NextResponse.redirect(new URL("/admin/settings?discord=unconfigured", req.url));
  }
  const origin = process.env.WEB_BASE_URL || new URL(req.url).origin;
  const redirectUri = `${origin}/api/discord/oauth/callback`;
  const state = crypto.randomUUID();

  const url = new URL("https://discord.com/oauth2/authorize");
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "identify guilds");
  url.searchParams.set("state", state);

  const res = NextResponse.redirect(url);
  res.cookies.set("dc_oauth_state", state, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 600,
  });
  return res;
}
