import { clerkEnabled } from "../../../components/AuthProvider";

export default function SignUpPage() {
  if (!clerkEnabled) {
    return (
      <main className="flex min-h-screen items-center justify-center text-white/60">
        Auth not configured — running in open mode.
      </main>
    );
  }
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { SignUp } = require("@clerk/nextjs");
  return (
    <main className="flex min-h-screen items-center justify-center bg-black">
      <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" forceRedirectUrl="/admin" />
    </main>
  );
}
