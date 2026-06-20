"""Central settings. Loads .env from repo root, falls back to process env.

Everything is optional at import time so the app boots without keys (tests run,
health works); each integration checks its own key when actually used.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# repo root = two levels up from this file (agent/app/config.py -> repo)
_REPO_ROOT = Path(__file__).resolve().parents[2]
# override=True so the repo .env is authoritative over any stale shell env vars
# (e.g. a pre-existing ANTHROPIC_API_KEY in the environment shadowing the funded one).
load_dotenv(_REPO_ROOT / ".env", override=True)
load_dotenv(_REPO_ROOT / ".env.local", override=True)  # local overrides win if present


class Settings:
    def __init__(self) -> None:
        # Anthropic
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.anthropic_model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        # Browserbase
        self.browserbase_api_key = os.environ.get("BROWSERBASE_API_KEY", "")
        self.browserbase_project_id = os.environ.get("BROWSERBASE_PROJECT_ID", "")
        # Deepgram
        self.deepgram_api_key = os.environ.get("DEEPGRAM_API_KEY", "")
        # Gemini (image generation + editing)
        self.gemini_api_key = (os.environ.get("GEMINI_API_KEY", "")
                               or os.environ.get("GOOGLE_API_KEY", ""))
        self.gemini_image_model = os.environ.get("GEMINI_IMAGE_MODEL",
                                                 "gemini-2.5-flash-image")
        # Fetch / ASI:One
        self.asi_one_api_key = os.environ.get("ASI_ONE_API_KEY", "")
        self.agentverse_api_key = os.environ.get("AGENTVERSE_API_KEY", "")
        self.uagent_seed = os.environ.get("UAGENT_SEED", "")
        # Upstash Redis
        self.upstash_url = os.environ.get("UPSTASH_REDIS_REST_URL", "")
        self.upstash_token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
        # Convex
        self.convex_url = os.environ.get("CONVEX_URL", "")
        # Slack
        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
        self.slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "")
        self.slack_alert_channel = os.environ.get("SLACK_ALERT_CHANNEL", "")
        # Discord (free alternative to Slack)
        self.discord_public_key = os.environ.get("DISCORD_PUBLIC_KEY", "")
        self.discord_bot_token = os.environ.get("DISCORD_BOT_TOKEN", "")
        self.discord_app_id = os.environ.get("DISCORD_APP_ID", "")
        self.discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
        # Daily (video + screen-share live sessions)
        self.daily_api_key = os.environ.get("DAILY_API_KEY", "")
        self.daily_domain = os.environ.get("DAILY_DOMAIN", "")
        # Twilio (SMS + phone-call interviews)
        self.twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.twilio_from_number = os.environ.get("TWILIO_FROM_NUMBER", "")
        # Vercel (FDE sandbox preview deploys)
        self.vercel_token = os.environ.get("VERCEL_TOKEN", "")
        # Team/scope slug — the Vercel CLI requires it in non-interactive mode.
        self.vercel_scope = os.environ.get("VERCEL_SCOPE", "")
        # Reddit OAuth (script app: reddit.com/prefs/apps) for .json monitoring
        self.reddit_client_id = os.environ.get("REDDIT_CLIENT_ID", "")
        self.reddit_client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
        # wiring
        self.agent_base_url = os.environ.get("AGENT_BASE_URL", "http://localhost:8000")
        self.web_base_url = os.environ.get("WEB_BASE_URL", "http://localhost:3000")
        self.shared_token = os.environ.get("AGENT_SHARED_TOKEN", "")

    @property
    def cors_origins(self) -> list[str]:
        return [self.web_base_url, "http://localhost:3000", "http://localhost:3001"]

    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)

    def has_convex(self) -> bool:
        return bool(self.convex_url)

    def has_redis(self) -> bool:
        return bool(self.upstash_url and self.upstash_token)

    def has_browserbase(self) -> bool:
        return bool(self.browserbase_api_key and self.browserbase_project_id)

    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
