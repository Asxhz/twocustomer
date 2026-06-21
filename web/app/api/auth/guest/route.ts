import { NextResponse } from "next/server";
import { convexQuery, convexMutation } from "@/lib/convexApi";
import { mintSession, SESSION_COOKIE, sessionCookieOptions } from "@/lib/session";

interface BrandRow { companyId?: string }

// Guest customer access (e.g. from a Discord invite link). No password: mints a
// short-lived customer session scoped to a brand's company so /u works instantly.
interface InviteRow { used?: boolean; brand?: string }

export async function POST(req: Request) {
  const { brand, email, invite } = await req.json().catch(() => ({}));
  // Single-use invite: reject if already used, else mark it used now.
  let slug = (brand || "").toString().trim();
  if (invite) {
    const inv = await convexQuery<InviteRow | null>("invites:get", { id: invite });
    if (inv?.used) {
      return NextResponse.json({ error: "This link was already used." }, { status: 410 });
    }
    if (inv?.brand && !slug) slug = inv.brand;
    await convexMutation("invites:markUsed", { id: invite });
  }
  let companyId: string | undefined;
  if (slug) {
    const b = await convexQuery<BrandRow | null>("brands:getBySlug", { slug });
    companyId = b?.companyId;
  }
  const guestEmail = (email || `guest+${Math.abs(hashStr(slug))}@guest.local`)
    .toString()
    .trim()
    .toLowerCase()
    .slice(0, 160);

  await convexMutation("users:upsert", {
    email: guestEmail, role: "customer", companyId,
  });
  const token = await mintSession(guestEmail, "customer", companyId, true);
  const res = NextResponse.json({ ok: true, role: "customer" });
  res.cookies.set(SESSION_COOKIE, token, sessionCookieOptions);
  return res;
}

// Math.random/Date.now are unavailable in some runtimes; derive a stable id.
function hashStr(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return h || 1;
}
