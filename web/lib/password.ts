// Password hashing with PBKDF2-SHA256 (Web Crypto, runs in Node + edge).
// Stored form: "pbkdf2$<iterations>$<saltB64>$<hashB64>".

const enc = new TextEncoder();
const ITER = 120_000;

function b64(bytes: Uint8Array): string {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s);
}
function unb64(s: string): Uint8Array {
  return Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
}
const buf = (b: Uint8Array): BufferSource => b as unknown as BufferSource;

async function derive(password: string, salt: Uint8Array, iter: number): Promise<Uint8Array> {
  const key = await crypto.subtle.importKey("raw", buf(enc.encode(password)), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt: buf(salt), iterations: iter, hash: "SHA-256" },
    key,
    256,
  );
  return new Uint8Array(bits);
}

export async function hashPassword(password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const hash = await derive(password, salt, ITER);
  return `pbkdf2$${ITER}$${b64(salt)}$${b64(hash)}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  try {
    const [scheme, iterStr, saltB64, hashB64] = stored.split("$");
    if (scheme !== "pbkdf2") return false;
    const got = await derive(password, unb64(saltB64), parseInt(iterStr, 10));
    const want = unb64(hashB64);
    if (got.length !== want.length) return false;
    let diff = 0;
    for (let i = 0; i < got.length; i++) diff |= got[i] ^ want[i];
    return diff === 0;
  } catch {
    return false;
  }
}

export function validPassword(p: string): boolean {
  return typeof p === "string" && p.length >= 8;
}
