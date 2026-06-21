import { NextResponse } from "next/server";
import { convexQueryStatus, convexQuery, convexConfigured } from "@/lib/convexApi";
import { verifyPassword } from "@/lib/password";
import { mintSession, SESSION_COOKIE, sessionCookieOptions } from "@/lib/session";

interface UserRow { _id: string; role: string; companyId?: string; passwordHash?: string }
interface CompanyRow { _id: string; setupComplete?: boolean }

// Log in: verify email + password against the stored hash. No auto-provisioning.
export async function POST(req: Request) {
  const { email, password } = await req.json().catch(() => ({}));
  const value = (email || "").toString().trim().toLowerCase().slice(0, 160);

  const lookup = await convexQueryStatus<UserRow | null>("users:getByEmail", { email: value });
  if (convexConfigured && !lookup.ok) {
    return NextResponse.json({ error: "Service unavailable, try again." }, { status: 503 });
  }
  const user = lookup.value;
  if (!user || !user.passwordHash || !(await verifyPassword(password || "", user.passwordHash))) {
    return NextResponse.json({ error: "Wrong email or password." }, { status: 401 });
  }

  const role = user.role === "admin" ? "admin" : "customer";
  let setup = role === "customer";
  if (role === "admin" && user.companyId) {
    const co = await convexQuery<CompanyRow | null>("companies:get", { id: user.companyId });
    setup = Boolean(co?.setupComplete);
  }

  const token = await mintSession(value, role, user.companyId, setup);
  const res = NextResponse.json({ ok: true, role, companyId: user.companyId ?? null });
  res.cookies.set(SESSION_COOKIE, token, sessionCookieOptions);
  return res;
}
