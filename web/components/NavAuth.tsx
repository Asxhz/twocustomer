import Link from "next/link";

// Renders Clerk's sign-in / user button only when Clerk is configured.
// Falls back to the open "Customer view" link otherwise.
const clerkOn = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

export default function NavAuth() {
  if (!clerkOn) {
    return (
      <Link
        href="/u"
        className="rounded-md border border-white/15 px-3 py-1 text-xs text-white/70 hover:text-white"
      >
        Customer view
      </Link>
    );
  }
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { SignedIn, SignedOut, UserButton, SignInButton } = require("@clerk/nextjs");
  return (
    <div className="flex items-center gap-3">
      <Link
        href="/u"
        className="rounded-md border border-white/15 px-3 py-1 text-xs text-white/70 hover:text-white"
      >
        Customer view
      </Link>
      <SignedOut>
        <SignInButton mode="modal">
          <button className="rounded-md bg-emerald-500 px-3 py-1 text-xs font-medium text-black hover:bg-emerald-400">
            Sign in
          </button>
        </SignInButton>
      </SignedOut>
      <SignedIn>
        <UserButton afterSignOutUrl="/" />
      </SignedIn>
    </div>
  );
}
