import { NextResponse } from "next/server";
import { convexQueryStatus, convexMutation, convexConfigured } from "@/lib/convexApi";
import { hashPassword, validPassword } from "@/lib/password";
import { mintSession, SESSION_COOKIE, sessionCookieOptions } from "@/lib/session";

interface UserRow { _id: string; passwordHash?: string }

// Create a real account: email + password. First user is the admin of a new
// company and lands in setup.
export async function POST(req: Request) {
  const { email, password } = await req.json().catch(() => ({}));
  const value = (email || "").toString().trim().toLowerCase().slice(0, 160);
  if (!value || !value.includes("@")) {
    return NextResponse.json({ error: "Enter a valid email." }, { status: 400 });
  }
  if (!validPassword(password)) {
    return NextResponse.json({ error: "Password must be at least 8 characters." }, { status: 400 });
  }

  const lookup = await convexQueryStatus<UserRow | null>("users:getByEmail", { email: value });
  if (convexConfigured && !lookup.ok) {
    return NextResponse.json({ error: "Service unavailable, try again." }, { status: 503 });
  }
  if (lookup.value?.passwordHash) {
    return NextResponse.json({ error: "Account already exists. Log in instead." }, { status: 409 });
  }

  const passwordHash = await hashPassword(password);
  // Don't pass setupComplete: upsert only patches provided keys, so an existing
  // (already set-up) company is never reset back to the wizard.
  const companyId = await convexMutation<string>("companies:upsert", {
    name: `${value.split("@")[0] || "My"} workspace`,
    ownerEmail: value,
  });
  await convexMutation("users:upsert", {
    email: value, role: "admin", companyId: companyId ?? undefined, passwordHash,
  });

  // Carry the real setup state so already-set-up founders skip the wizard.
  const co = companyId
    ? await convexQueryStatus<{ setupComplete?: boolean }>("companies:get", { id: companyId })
    : { ok: false, value: null };
  const setup = Boolean(co.value?.setupComplete);

  const token = await mintSession(value, "admin", companyId ?? undefined, setup);
  const res = NextResponse.json({ ok: true, role: "admin", setup });
  res.cookies.set(SESSION_COOKIE, token, sessionCookieOptions);
  return res;
}
