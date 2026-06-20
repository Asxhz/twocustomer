import { NextResponse } from "next/server";

// Email-only sign-in: store the email in a cookie. No password, no provider.
export async function POST(req: Request) {
  const { email } = await req.json().catch(() => ({ email: "" }));
  const value = (email || "founder@twocustomer.app").toString().slice(0, 120);
  const res = NextResponse.json({ ok: true, email: value });
  res.cookies.set("tc_user", value, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7, // 7 days
  });
  return res;
}
