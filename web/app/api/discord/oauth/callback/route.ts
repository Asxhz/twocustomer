import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getSession } from "@/lib/session";
import { convexMutation } from "@/lib/convexApi";
import { encryptSecret } from "@/lib/crypto";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const cookieState = (await cookies()).get("dc_oauth_state")?.value;
  const session = await getSession();

  const back = (q: string) => NextResponse.redirect(new URL(`/admin/settings?discord=${q}`, req.url));

  if (!session?.companyId) return NextResponse.redirect(new URL("/sign-in", req.url));
  if (!code || !state || state !== cookieState) return back("error");

  const clientId = process.env.DISCORD_CLIENT_ID;
  const clientSecret = process.env.DISCORD_CLIENT_SECRET;
  if (!clientId || !clientSecret) return back("unconfigured");
  const origin = process.env.WEB_BASE_URL || url.origin;

  try {
    const tokenRes = await fetch("https://discord.com/api/oauth2/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: clientId,
        client_secret: clientSecret,
        grant_type: "authorization_code",
        code,
        redirect_uri: `${origin}/api/discord/oauth/callback`,
      }),
    });
    const tok = await tokenRes.json();
    const accessToken: string | undefined = tok.access_token;
    if (!accessToken) return back("error");

    // First guild the user is in = the brand's server (best-effort).
    let guild = "";
    try {
      const gRes = await fetch("https://discord.com/api/users/@me/guilds", {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const guilds = await gRes.json();
      if (Array.isArray(guilds) && guilds[0]) guild = `${guilds[0].name} (${guilds[0].id})`;
    } catch {
      /* guild optional */
    }

    await convexMutation("companies:setDiscord", {
      id: session.companyId,
      discordGuild: guild || undefined,
      discordTokenEnc: await encryptSecret(accessToken),
    });
    return back("connected");
  } catch {
    return back("error");
  }
}
