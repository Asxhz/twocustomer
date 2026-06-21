// Signed, Redis-backed sessions. The cookie holds an HMAC-signed token
// {sid,email,role,companyId,exp}; the sid is also written to Upstash Redis so a
// session can be revoked server-side. Verification uses Web Crypto so it runs in
// both the Node route handlers and the (edge) middleware. When Upstash isn't
// configured the signed token still stands on its own (stateless fallback) so the
// app never hard-breaks in local dev.

import type { NextRequest } from "next/server";

export const SESSION_COOKIE = "tc_sess";
const MAX_AGE = 60 * 60 * 24 * 7; // 7 days

export interface Session {
  sid: string;
  email: string;
  role: "admin" | "customer";
  companyId?: string;
  setup?: boolean; // company setup wizard completed (admins)
  exp: number; // unix seconds
}

function secret(): string {
  return (
    process.env.SESSION_SECRET ||
    process.env.AGENT_SHARED_TOKEN ||
    "tc-dev-insecure-secret"
  );
}

const enc = new TextEncoder();

function b64urlEncode(bytes: Uint8Array): string {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function b64urlEncodeStr(str: string): string {
  return b64urlEncode(enc.encode(str));
}
function b64urlDecodeStr(s: string): string {
  const pad = s.replace(/-/g, "+").replace(/_/g, "/");
  return atob(pad + "=".repeat((4 - (pad.length % 4)) % 4));
}

async function hmacKey(): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    enc.encode(secret()),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"],
  );
}

async function signToken(payload: Session): Promise<string> {
  const body = b64urlEncodeStr(JSON.stringify(payload));
  const key = await hmacKey();
  const sig = new Uint8Array(
    await crypto.subtle.sign("HMAC", key, enc.encode(body)),
  );
  return `${body}.${b64urlEncode(sig)}`;
}

async function verifyToken(token: string): Promise<Session | null> {
  const dot = token.lastIndexOf(".");
  if (dot < 0) return null;
  const body = token.slice(0, dot);
  const sigPart = token.slice(dot + 1);
  try {
    const key = await hmacKey();
    const sigBytes = Uint8Array.from(b64urlDecodeStr(sigPart), (c) =>
      c.charCodeAt(0),
    );
    const ok = await crypto.subtle.verify(
      "HMAC",
      key,
      sigBytes,
      enc.encode(body),
    );
    if (!ok) return null;
    const payload = JSON.parse(b64urlDecodeStr(body)) as Session;
    if (!payload.exp || payload.exp < Math.floor(Date.now() / 1000)) return null;
    return payload;
  } catch {
    return null;
  }
}

// --- Upstash (best-effort revocation list) -----------------------------------

const UP_URL = (process.env.UPSTASH_REDIS_REST_URL || "").replace(/\/$/, "");
const UP_TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN || "";
const redisOn = Boolean(UP_URL && UP_TOKEN);

async function redisCmd(...args: string[]): Promise<unknown> {
  if (!redisOn) return null;
  try {
    const r = await fetch(UP_URL, {
      method: "POST",
      headers: { Authorization: `Bearer ${UP_TOKEN}` },
      body: JSON.stringify(args),
      cache: "no-store",
    });
    if (!r.ok) return null;
    return (await r.json()).result;
  } catch {
    return null;
  }
}

// --- Public API --------------------------------------------------------------

export async function mintSession(
  email: string,
  role: "admin" | "customer",
  companyId?: string,
  setup?: boolean,
): Promise<string> {
  const sid = crypto.randomUUID();
  const payload: Session = {
    sid,
    email,
    role,
    companyId,
    setup,
    exp: Math.floor(Date.now() / 1000) + MAX_AGE,
  };
  await redisCmd("set", `sess:${sid}`, email, "EX", String(MAX_AGE));
  return signToken(payload);
}

// Signature-only check (fast, no network). Use in the proxy for optimistic
// redirects. per Next.js guidance, the proxy must not do slow data fetching.
export async function peekToken(token: string | undefined): Promise<Session | null> {
  if (!token) return null;
  return verifyToken(token);
}

// Authoritative check: verify signature + (when Redis is on) confirm the sid
// hasn't been revoked server-side. Use in route handlers & server components.
export async function readToken(token: string | undefined): Promise<Session | null> {
  if (!token) return null;
  const s = await verifyToken(token);
  if (!s) return null;
  if (redisOn) {
    const live = await redisCmd("get", `sess:${s.sid}`);
    if (live === null) return null; // revoked / expired server-side
  }
  return s;
}

export async function revokeSession(sid: string): Promise<void> {
  await redisCmd("del", `sess:${sid}`);
}

// For the proxy (NextRequest). optimistic, signature-only (no Redis round-trip).
export async function getSessionFromRequest(
  req: NextRequest,
): Promise<Session | null> {
  return peekToken(req.cookies.get(SESSION_COOKIE)?.value);
}

// For route handlers & server components (next/headers).
export async function getSession(): Promise<Session | null> {
  const { cookies } = await import("next/headers");
  return readToken((await cookies()).get(SESSION_COOKIE)?.value);
}

export const sessionCookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  path: "/",
  secure: process.env.NODE_ENV === "production",
  maxAge: MAX_AGE,
};
