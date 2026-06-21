import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";

export async function GET() {
  const s = await getSession();
  if (!s) return NextResponse.json({ email: null, role: null, companyId: null });
  return NextResponse.json({
    email: s.email,
    role: s.role,
    companyId: s.companyId ?? null,
  });
}
