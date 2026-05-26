from __future__ import annotations

import asyncio
import sys

from app.bot import CoachBot
from app.config import ensure_db_path, load_config
from app.database import Database
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

    bot = CoachBot(config, db, kb=kb)
    await bot.start_bot()

    if config.bot_mode == "development":
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("shutdown_requested")
        finally:
            await bot.stop_bot()
            await db.close()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
