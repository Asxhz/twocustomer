import type { ReactNode } from "react";

// ClerkProvider only mounts when a publishable key is configured. Without it,
// the app runs open (no login wall) so the demo build never breaks on missing
// auth keys.
const clerkOn = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

export default function AuthProvider({ children }: { children: ReactNode }) {
  if (!clerkOn) return <>{children}</>;
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { ClerkProvider } = require("@clerk/nextjs");
  return (
    <ClerkProvider
      appearance={{ variables: { colorPrimary: "#34d399" } }}
    >
      {children}
    </ClerkProvider>
  );
}

export const clerkEnabled = clerkOn;
