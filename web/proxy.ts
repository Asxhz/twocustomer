import { NextResponse, type NextRequest } from "next/server";

// Clerk login is optional: it activates only when the publishable key is set,
// so the app still runs (open) without Clerk configured. When configured, it
// protects the brand console.
const clerkOn = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

let handler: (req: NextRequest) => Response | Promise<Response>;

if (clerkOn) {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { clerkMiddleware, createRouteMatcher } = require("@clerk/nextjs/server");
  const isProtected = createRouteMatcher(["/admin(.*)", "/sessions(.*)"]);
  handler = clerkMiddleware(
    async (auth: { protect: () => Promise<unknown> }, req: NextRequest) => {
      if (isProtected(req)) await auth.protect();
    },
  );
} else {
  handler = () => NextResponse.next();
}

export default handler;

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)", "/(api|trpc)(.*)"],
};
