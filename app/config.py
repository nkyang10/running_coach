from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    telegram_bot_token: str
    openai_api_key: str
    discord_bot_token: str | None = None
    anthropic_api_key: str | None = None
    admin_chat_ids: list[int] = field(default_factory=list)
    bot_mode: str = "development"
    coach_db_path: str = "data/coach.db"
    coach_knowledge_path: str = "knowledge/"
    qc_interval_minutes: int = 60
    coach_use_real_llm: bool = False
    garmin_client_id: str | None = None
    garmin_client_secret: str | None = None
    strava_client_id: str | None = None
    strava_client_secret: str | None = None
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None


def load_config(env_file: str | None = None) -> Config:
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")

    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY is required")

    admin_ids_str = os.getenv("ADMIN_CHAT_IDS", "")
    if not admin_ids_str:
        raise ValueError("ADMIN_CHAT_IDS is required")

    admin_ids = []
    for part in admin_ids_str.split(","):
        part = part.strip()
        if part:
            try:
                admin_ids.append(int(part))
            except ValueError:
                pass

    if not admin_ids:
        raise ValueError("ADMIN_CHAT_IDS must contain at least one valid chat ID")

    mode = os.getenv("BOT_MODE", "development")
    if mode not in ("development", "production", "test"):
        mode = "development"

    db_path = os.getenv("COACH_DB_PATH", "data/coach.db")
    kb_path = os.getenv("COACH_KNOWLEDGE_PATH", "knowledge/")

    qc_interval_str = os.getenv("QC_INTERVAL_MINUTES", "60")
    try:
        qc_interval = int(qc_interval_str)
    except ValueError:
        qc_interval = 60

    use_real_llm = os.getenv("COACH_USE_REAL_LLM", "false").lower() in (
        "true",
        "1",
        "yes",
    )

    return Config(
        telegram_bot_token=token,
        openai_api_key=openai_key,
        discord_bot_token=os.getenv("DISCORD_BOT_TOKEN") or None,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        admin_chat_ids=admin_ids,
        bot_mode=mode,
        coach_db_path=db_path,
        coach_knowledge_path=kb_path,
        qc_interval_minutes=qc_interval,
        coach_use_real_llm=use_real_llm,
        garmin_client_id=os.getenv("GARMIN_CLIENT_ID"),
        garmin_client_secret=os.getenv("GARMIN_CLIENT_SECRET"),
        strava_client_id=os.getenv("STRAVA_CLIENT_ID"),
        strava_client_secret=os.getenv("STRAVA_CLIENT_SECRET"),
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY"),
        stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET"),
    )


def ensure_db_path(path: str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
