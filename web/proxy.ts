import { NextResponse, type NextRequest } from "next/server";
import { getSessionFromRequest } from "@/lib/session";

// Route gate. /admin/* is admin-only; /u/* needs any authenticated user.
// Unauthenticated users are sent to /sign-in?next=<path>. Authoritative checks
// also run server-side in route handlers / layouts — this is the UX redirect.
export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const session = await getSessionFromRequest(req);

  const wantsAdmin = pathname.startsWith("/admin");
  const wantsCustomer = pathname.startsWith("/u");

  if (!session) {
    const url = req.nextUrl.clone();
    url.pathname = "/sign-in";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  if (wantsAdmin && session.role !== "admin") {
    // A signed-in customer hitting the console → send to their surface.
    const url = req.nextUrl.clone();
    url.pathname = "/u";
    url.search = "";
    return NextResponse.redirect(url);
  }

  // Admin must finish the setup wizard before the rest of the console works.
  if (
    wantsAdmin &&
    session.role === "admin" &&
    session.setup === false &&
    pathname !== "/admin/setup"
  ) {
    const url = req.nextUrl.clone();
    url.pathname = "/admin/setup";
    url.search = "";
    return NextResponse.redirect(url);
  }

  if (wantsCustomer && !session) {
    const url = req.nextUrl.clone();
    url.pathname = "/sign-in";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*", "/u/:path*"],
};
