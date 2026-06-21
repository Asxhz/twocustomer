"""Decrypt secrets the web stored (AES-GCM), e.g. the founder's GitHub token.

Mirrors web/lib/crypto.ts exactly:
  key  = SHA-256(SESSION_SECRET || AGENT_SHARED_TOKEN || "tc-dev-insecure-secret")
  blob = base64(iv) "." base64(ciphertext+tag)   (12-byte iv, GCM tag appended)
When SESSION_SECRET is unset on both sides they share AGENT_SHARED_TOKEN, so the
keys match and the agent can read what the web wrote.
"""

from __future__ import annotations

import base64
import hashlib
import os

from app.config import get_settings


def _key() -> bytes:
    secret = (os.environ.get("SESSION_SECRET")
              or get_settings().agent_shared_token
              or "tc-dev-insecure-secret")
    return hashlib.sha256(secret.encode()).digest()


def decrypt_secret(blob: str) -> str | None:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        iv_b64, ct_b64 = blob.split(".", 1)
        iv = base64.b64decode(iv_b64)
        ct = base64.b64decode(ct_b64)
        pt = AESGCM(_key()).decrypt(iv, ct, None)
        return pt.decode("utf-8")
    except Exception:  # noqa: BLE001 - bad/unreadable blob
        return None
