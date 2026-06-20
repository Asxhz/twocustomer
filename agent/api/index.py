"""Vercel serverless entrypoint — exposes the FastAPI ASGI app."""

import os
import sys

# Make the agent package importable (project root = agent/).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

__all__ = ["app"]
