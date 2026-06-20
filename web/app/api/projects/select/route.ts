import { NextResponse } from "next/server";

// Switch the active project (caches it in the tc_project cookie).
export async function POST(req: Request) {
  const { slug } = await req.json().catch(() => ({ slug: "" }));
  const value = (slug || "").toString().trim();
  if (!value) return NextResponse.json({ error: "slug required" }, { status: 400 });
  const res = NextResponse.json({ ok: true, slug: value });
  res.cookies.set("tc_project", value, {
    httpOnly: false, sameSite: "lax", path: "/", maxAge: 60 * 60 * 24 * 30,
  });
  return res;
}
