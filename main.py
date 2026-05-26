from __future__ import annotations

import asyncio
import sys

from app.bot import CoachBot
from app.coach import CoachEngine
from app.coach_service import CoachService
from app.config import ensure_db_path, load_config
from app.database import Database
from app.discord_bot import DiscordBot
from app.knowledge import KnowledgeBase
from app.logger import get_logger, setup_logging

logger = get_logger(__name__)


async def main() -> int:
    config = load_config()

    if config.bot_mode == "test":
        import pytest
        logger.info("starting_test_mode")
        exit_code = pytest.main(["-v", "tests/"])
        return exit_code if exit_code is not None else 0

    log_level = "DEBUG" if config.bot_mode == "development" else "INFO"
    log_file = None if config.bot_mode == "development" else "data/logs/coach.log"
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        console=True,
    )

    logger.info(
        "starting_coach",
        mode=config.bot_mode,
        db_path=config.coach_db_path,
    )

    db_path = ensure_db_path(config.coach_db_path)
    db = Database(db_path)
    await db.connect()
    await db.init_tables()
    logger.info("database_ready")

    kb = KnowledgeBase(config.coach_knowledge_path)
    kb.load()
    logger.info("knowledge_loaded", count=len(kb.get_all()))

    coach = CoachEngine(config, db, kb)
    service = CoachService(config, db, kb, coach)
    logger.info("coach_engine_ready")

    telegram_bot = CoachBot(config, db, kb=kb, coach=coach)
    await telegram_bot.start_bot()
    logger.info("telegram_bot_started")

    discord_bot = None
    if config.discord_bot_token:
        discord_bot = DiscordBot(config, service)
        logger.info("discord_bot_starting")
        asyncio.create_task(discord_bot.start(config.discord_bot_token))
        logger.info("discord_bot_started")
    else:
        logger.info("discord_bot_disabled_no_token")

    if config.bot_mode == "development":
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("shutdown_requested")
        finally:
            await telegram_bot.stop_bot()
            await db.close()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
