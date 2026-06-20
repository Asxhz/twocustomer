import { NextResponse } from "next/server";
import { cookies } from "next/headers";

export async function GET() {
  const email = (await cookies()).get("tc_user")?.value ?? null;
  return NextResponse.json({ email });
}
