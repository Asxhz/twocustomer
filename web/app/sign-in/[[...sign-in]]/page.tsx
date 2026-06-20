import { clerkEnabled } from "../../../components/AuthProvider";

export default function SignInPage() {
  if (!clerkEnabled) {
    return (
      <main className="flex min-h-screen items-center justify-center text-white/60">
        Auth not configured — running in open mode.
      </main>
    );
  }
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { SignIn } = require("@clerk/nextjs");
  return (
    <main className="flex min-h-screen items-center justify-center bg-black">
      <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" forceRedirectUrl="/admin" />
    </main>
  );
}
