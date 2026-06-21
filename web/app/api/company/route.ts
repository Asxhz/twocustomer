import { NextResponse } from "next/server";
import { getSession, mintSession, SESSION_COOKIE, sessionCookieOptions } from "@/lib/session";
import { convexQuery, convexMutation } from "@/lib/convexApi";

interface CompanyRow {
  _id: string;
  name: string;
  ownerEmail: string;
  githubLogin?: string;
  discordGuild?: string;
  setupComplete?: boolean;
}

export async function GET() {
  const s = await getSession();
  if (!s?.companyId) return NextResponse.json({ company: null });
  const company = await convexQuery<CompanyRow | null>("companies:get", { id: s.companyId });
  return NextResponse.json({
    company: company
      ? {
          name: company.name,
          githubLogin: company.githubLogin ?? null,
          discordGuild: company.discordGuild ?? null,
          setupComplete: Boolean(company.setupComplete),
        }
      : null,
  });
}

// Update profile fields and/or finish setup. Admin only.
export async function POST(req: Request) {
  const s = await getSession();
  if (!s?.companyId || s.role !== "admin") {
    return NextResponse.json({ ok: false }, { status: 403 });
  }
  const body = await req.json().catch(() => ({}));
  if (body.name || body.discordGuild !== undefined) {
    await convexMutation("companies:update", {
      id: s.companyId,
      name: body.name ? body.name.toString() : undefined,
      discordGuild: body.discordGuild !== undefined ? body.discordGuild.toString() : undefined,
    });
  }
  if (body.setupComplete) {
    await convexMutation("companies:markSetupComplete", { id: s.companyId });
    // Re-mint the session so the proxy stops gating to /admin/setup.
    const token = await mintSession(s.email, s.role, s.companyId, true);
    const res = NextResponse.json({ ok: true });
    res.cookies.set(SESSION_COOKIE, token, sessionCookieOptions);
    return res;
  }
  return NextResponse.json({ ok: true });
}
