import { NextResponse, type NextRequest } from "next/server";

// Dead-simple demo auth: the brand console (/admin, /sessions) needs a
// `tc_user` cookie, set by the email-only sign-in. No provider, no password.
const GATED = [/^\/admin/, /^\/sessions/];

export default function proxy(req: NextRequest) {
  const path = req.nextUrl.pathname;
  if (GATED.some((re) => re.test(path)) && !req.cookies.get("tc_user")) {
    const url = req.nextUrl.clone();
    url.pathname = "/sign-in";
    url.searchParams.set("next", path);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)", "/(api|trpc)(.*)"],
};
