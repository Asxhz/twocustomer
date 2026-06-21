// AES-GCM encrypt/decrypt for secrets at rest (e.g. GitHub OAuth tokens stored
// in Convex). Key derived from SESSION_SECRET. Web Crypto → runs in Node + edge.

const enc = new TextEncoder();
const dec = new TextDecoder();

// Web Crypto wants ArrayBuffer-backed BufferSource; TS 5.7 treats the encoder's
// Uint8Array as ArrayBufferLike. This cast keeps the calls type-clean.
const buf = (b: Uint8Array): BufferSource => b as unknown as BufferSource;

function secret(): string {
  return (
    process.env.SESSION_SECRET ||
    process.env.AGENT_SHARED_TOKEN ||
    "tc-dev-insecure-secret"
  );
}

async function aesKey(): Promise<CryptoKey> {
  const hash = await crypto.subtle.digest("SHA-256", buf(enc.encode(secret())));
  return crypto.subtle.importKey("raw", hash, { name: "AES-GCM" }, false, [
    "encrypt",
    "decrypt",
  ]);
}

function toB64(b: Uint8Array): string {
  let s = "";
  for (const x of b) s += String.fromCharCode(x);
  return btoa(s);
}
function fromB64(s: string): Uint8Array {
  return Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
}

// Returns "iv.ciphertext" (both base64).
export async function encryptSecret(plain: string): Promise<string> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await aesKey();
  const ct = new Uint8Array(
    await crypto.subtle.encrypt({ name: "AES-GCM", iv: buf(iv) }, key, buf(enc.encode(plain))),
  );
  return `${toB64(iv)}.${toB64(ct)}`;
}

export async function decryptSecret(blob: string): Promise<string | null> {
  try {
    const [ivB64, ctB64] = blob.split(".");
    const iv = fromB64(ivB64);
    const ct = fromB64(ctB64);
    const key = await aesKey();
    const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: buf(iv) }, key, buf(ct));
    return dec.decode(pt);
  } catch {
    return null;
  }
}
