"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function NavAuth() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((d) => setEmail(d.email))
      .catch(() => setEmail(null))
      .finally(() => setLoaded(true));
  }, []);

  async function signOut() {
    await fetch("/api/auth/logout", { method: "POST" });
    setEmail(null);
    router.push("/");
    router.refresh();
  }

  return (
    <div className="flex items-center gap-3">
      <Link
        href="/u"
        className="rounded-md border border-white/15 px-3 py-1 text-xs text-white/70 hover:text-white"
      >
        Customer view
      </Link>
      {!loaded ? null : email ? (
        <>
          <span className="hidden text-xs text-white/40 sm:inline">{email}</span>
          <button
            onClick={signOut}
            className="rounded-md border border-white/15 px-3 py-1 text-xs text-white/70 hover:text-white"
          >
            Sign out
          </button>
        </>
      ) : (
        <Link
          href="/sign-in"
          className="rounded-md bg-emerald-500 px-3 py-1 text-xs font-medium text-black hover:bg-emerald-400"
        >
          Sign in
        </Link>
      )}
    </div>
  );
}
