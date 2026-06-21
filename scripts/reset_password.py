"""Reset (or set) a founder account password.

Hashes the password with the same PBKDF2-SHA256 scheme the web app uses
(web/lib/password.ts): pbkdf2$<iter>$<saltB64>$<hashB64>, then upserts the user
row in Convex so login works immediately.

Usage:
    python scripts/reset_password.py <email> <password> [--role admin]

Run from the repo root with the agent venv + .env loaded, e.g.:
    set -a; source .env; set +a
    agent/.venv/bin/python scripts/reset_password.py ashmit@berkeley.edu 'TwoCustomer2026!'
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import sys

ITER = 120_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITER, dklen=32)
    return f"pbkdf2${ITER}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


async def main() -> int:
    if len(sys.argv) < 3:
        print("usage: reset_password.py <email> <password> [--role admin]")
        return 2
    email = sys.argv[1].strip().lower()
    password = sys.argv[2]
    role = "admin"
    if "--role" in sys.argv:
        role = sys.argv[sys.argv.index("--role") + 1]

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
    from app.state.convex_client import get_convex

    cx = get_convex()
    if not cx.enabled:
        print("Convex is not configured (set CONVEX_URL). Cannot reset.")
        return 1

    pw_hash = hash_password(password)
    await cx.mutation("users:upsert", email=email, passwordHash=pw_hash, role=role)
    print(f"OK: set password for {email} (role={role}).")
    print(f"Login with: {email} / {password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
