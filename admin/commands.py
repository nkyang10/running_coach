from __future__ import annotations

from telegram.ext import CommandHandler

from app.bot import CoachBot
from app.logger import get_logger

logger = get_logger(__name__)


def register_admin_commands(bot: CoachBot) -> None:
    app = bot.application
    if not app:
        logger.error("cannot_register_commands_no_app")
        return

    handlers = [
        CommandHandler("admin_status", bot.cmd_admin_status),
        CommandHandler("admin_health", bot.cmd_admin_health),
        CommandHandler("admin_help", bot.cmd_admin_help),
        CommandHandler("admin_reload", bot.cmd_admin_reload),
        CommandHandler("admin_backup", bot.cmd_admin_backup),
        CommandHandler("admin_knowledge", bot.cmd_admin_knowledge),
    ]

    for handler in handlers:
        app.add_handler(handler)

    logger.info("admin_commands_registered")
