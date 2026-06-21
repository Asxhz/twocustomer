// Server-side Convex access over the HTTP API (query + mutation). No codegen.
// Returns null on any failure so callers can degrade gracefully.

const CONVEX_URL = (process.env.CONVEX_URL || "").replace(/\/$/, "");

export const convexConfigured = Boolean(CONVEX_URL);

async function call<T>(
  kind: "query" | "mutation",
  path: string,
  args: Record<string, unknown>,
): Promise<T | null> {
  if (!CONVEX_URL) return null;
  try {
    const res = await fetch(`${CONVEX_URL}/api/${kind}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path, args, format: "json" }),
      cache: "no-store",
    });
    if (!res.ok) return null;
    const body = await res.json();
    return body.status === "success" ? (body.value as T) : null;
  } catch {
    return null;
  }
}

export function convexQuery<T>(path: string, args: Record<string, unknown> = {}) {
  return call<T>("query", path, args);
}

// Status-aware variant: ok=false means a transport/Convex error (NOT "no row").
// Lets callers (e.g. login) avoid treating "backend down" as "new user".
export async function convexQueryStatus<T>(
  path: string,
  args: Record<string, unknown> = {},
): Promise<{ ok: boolean; value: T | null }> {
  if (!CONVEX_URL) return { ok: false, value: null };
  try {
    const res = await fetch(`${CONVEX_URL}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path, args, format: "json" }),
      cache: "no-store",
    });
    if (!res.ok) return { ok: false, value: null };
    const body = await res.json();
    if (body.status !== "success") return { ok: false, value: null };
    return { ok: true, value: body.value as T };
  } catch {
    return { ok: false, value: null };
  }
}

export function convexMutation<T>(path: string, args: Record<string, unknown> = {}) {
  return call<T>("mutation", path, args);
}
