import { NextResponse } from "next/server";
import { getSession, revokeSession, SESSION_COOKIE } from "@/lib/session";

export async function POST() {
  const s = await getSession();
  if (s) await revokeSession(s.sid);
  const res = NextResponse.json({ ok: true });
  res.cookies.delete(SESSION_COOKIE);
  return res;
}
