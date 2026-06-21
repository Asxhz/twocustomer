import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { convexQuery, convexMutation } from "@/lib/convexApi";

interface Notif {
  _id: string;
  kind: string;
  title: string;
  body?: string;
  href?: string;
  read: boolean;
  ts: number;
}

// List the company's notifications (newest first).
export async function GET() {
  const s = await getSession();
  if (!s?.companyId) return NextResponse.json({ notifications: [], unread: 0 });
  const rows =
    (await convexQuery<Notif[]>("notifications:listByCompany", {
      companyId: s.companyId,
      limit: 30,
    })) ?? [];
  return NextResponse.json({
    notifications: rows,
    unread: rows.filter((n) => !n.read).length,
  });
}

// Mark one (id) or all read.
export async function POST(req: Request) {
  const s = await getSession();
  if (!s?.companyId) return NextResponse.json({ ok: false }, { status: 401 });
  const { id } = await req.json().catch(() => ({}));
  if (id) await convexMutation("notifications:markRead", { id });
  else await convexMutation("notifications:markAllRead", { companyId: s.companyId });
  return NextResponse.json({ ok: true });
}
