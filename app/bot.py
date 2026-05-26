from __future__ import annotations

from datetime import date
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import Config
from app.database import Database
from app.logger import get_logger
from app.models import PrimaryGoal, RunningLevel, Runner

logger = get_logger(__name__)

ONBOARDING_NAME, ONBOARDING_LEVEL, ONBOARDING_GOAL, ONBOARDING_WEEKLY_KM = range(4)


class CoachBot:
    def __init__(self, config: Config, db: Database) -> None:
        self.config = config
        self.db = db
        self.application: Optional[Application] = None

    async def start_bot(self) -> Application:
        app = Application.builder().token(self.config.telegram_bot_token).build()

        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("help", self.cmd_help))

        onboarding_conv = ConversationHandler(
            entry_points=[CommandHandler("start", self.cmd_start)],
            states={
                ONBOARDING_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.onboarding_name
                    )
                ],
                ONBOARDING_LEVEL: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.onboarding_level
                    )
                ],
                ONBOARDING_GOAL: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.onboarding_goal
                    )
                ],
                ONBOARDING_WEEKLY_KM: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.onboarding_weekly_km
                    )
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cmd_cancel)],
        )
        app.add_handler(onboarding_conv)

        app.add_handler(CommandHandler("admin_status", self.cmd_admin_status))
        app.add_handler(CommandHandler("admin_help", self.cmd_admin_help))

        self.application = app
        logger.info("bot_initialized")

        if self.config.bot_mode == "development":
            await app.initialize()
            await app.start()
            logger.info("bot_started_polling")
        return app

    async def stop_bot(self) -> None:
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
            logger.info("bot_stopped")

    def is_admin(self, chat_id: int) -> bool:
        return chat_id in self.config.admin_chat_ids

    async def reply(self, update: Update, text: str) -> None:
        if update.message:
            await update.message.reply_text(text)

    # ─── /start ───

    async def cmd_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        chat_id = update.effective_user.id if update.effective_user else 0
        existing = await self.db.get_runner(chat_id)

        if existing:
            welcome = (
                f"Welcome back, {existing.name or 'Runner'}!\n\n"
                f"Current program: {existing.current_program or 'None'}\n"
                f"Week {existing.week_of_program} | Phase: {existing.training_phase}\n"
                f"Total runs: {existing.total_runs}\n"
                f"30-day consistency: {existing.consistency_30d:.0%}\n\n"
                "Commands: /plan  /log  /status  /metrics  /history  /help"
            )
            await self.reply(update, welcome)
            return ConversationHandler.END

        await self.reply(
            update,
            "Welcome to AI Running Coach! 🏃\n\n"
            "Let's get to know you. What's your name?",
        )
        return ONBOARDING_NAME

    async def onboarding_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message or not update.message.text:
            return ONBOARDING_NAME
        context.user_data["onboard_name"] = update.message.text.strip()
        await self.reply(
            update,
            f"Nice to meet you, {context.user_data['onboard_name']}!\n\n"
            "What's your running level?\n"
            "1 - New (never run before)\n"
            "2 - Beginner (run occasionally)\n"
            "3 - Intermediate (run regularly)\n"
            "4 - Advanced (experienced runner)",
        )
        return ONBOARDING_LEVEL

    async def onboarding_level(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message or not update.message.text:
            return ONBOARDING_LEVEL
        text = update.message.text.strip()
        level_map = {
            "1": RunningLevel.NEW,
            "2": RunningLevel.BEGINNER,
            "3": RunningLevel.INTERMEDIATE,
            "4": RunningLevel.ADVANCED,
            "new": RunningLevel.NEW,
            "beginner": RunningLevel.BEGINNER,
            "intermediate": RunningLevel.INTERMEDIATE,
            "advanced": RunningLevel.ADVANCED,
        }
        level = level_map.get(text.lower())
        if not level:
            await self.reply(update, "Please enter 1, 2, 3, or 4.")
            return ONBOARDING_LEVEL
        context.user_data["onboard_level"] = level
        await self.reply(
            update,
            "What's your primary running goal?\n"
            "1 - Finish a 5K\n"
            "2 - Improve 5K time\n"
            "3 - Run a 10K\n"
            "4 - Half marathon\n"
            "5 - Marathon\n"
            "6 - General fitness",
        )
        return ONBOARDING_GOAL

    async def onboarding_goal(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message or not update.message.text:
            return ONBOARDING_GOAL
        text = update.message.text.strip()
        goal_map = {
            "1": PrimaryGoal.FINISH_5K,
            "2": PrimaryGoal.IMPROVE_5K,
            "3": PrimaryGoal.IMPROVE_10K,
            "4": PrimaryGoal.HALF_MARATHON,
            "5": PrimaryGoal.MARATHON,
            "6": PrimaryGoal.GENERAL,
            "finish 5k": PrimaryGoal.FINISH_5K,
            "improve 5k": PrimaryGoal.IMPROVE_5K,
            "10k": PrimaryGoal.IMPROVE_10K,
            "half marathon": PrimaryGoal.HALF_MARATHON,
            "marathon": PrimaryGoal.MARATHON,
            "general": PrimaryGoal.GENERAL,
        }
        goal = goal_map.get(text.lower())
        if not goal:
            await self.reply(update, "Please enter 1-6.")
            return ONBOARDING_GOAL
        context.user_data["onboard_goal"] = goal
        await self.reply(
            update,
            "How many km do you currently run per week? (enter 0 if just starting)",
        )
        return ONBOARDING_WEEKLY_KM

    async def onboarding_weekly_km(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message or not update.message.text:
            return ONBOARDING_WEEKLY_KM
        try:
            weekly_km = float(update.message.text.strip())
        except ValueError:
            await self.reply(update, "Please enter a number (e.g., 10 or 0).")
            return ONBOARDING_WEEKLY_KM

        chat_id = update.effective_user.id if update.effective_user else 0
        runner = Runner(
            chat_id=chat_id,
            name=context.user_data.get("onboard_name", "Runner"),
            running_level=context.user_data.get("onboard_level", RunningLevel.NEW),
            primary_goal=context.user_data.get("onboard_goal", PrimaryGoal.GENERAL),
            current_weekly_km=weekly_km,
            last_active=date.today(),
        )
        await self.db.create_runner(runner)

        await self.reply(
            update,
            f"Profile created! 🎉\n\n"
            f"Name: {runner.name}\n"
            f"Level: {runner.running_level.value}\n"
            f"Goal: {runner.primary_goal.value}\n"
            f"Weekly km: {runner.current_weekly_km}\n\n"
            "Commands: /plan  /log  /status  /metrics  /history  /help",
        )
        logger.info("onboarding_complete", chat_id=chat_id)
        return ConversationHandler.END

    # ─── /help ───

    async def cmd_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        text = (
            "🤖 AI Running Coach Commands\n\n"
            "/start - View profile or re-onboard\n"
            "/help - Show this message\n"
            "/plan - Generate a personalized training plan\n"
            "/log - Record a run (e.g., '5k in 25min, felt easy')\n"
            "/status - View your progress summary\n"
            "/metrics - Track body metrics (e.g., /metrics weight 72)\n"
            "/history - View recent runs\n\n"
            "💬 Just chat with me about your running!\n"
            "Admin commands available to authorized users."
        )
        await self.reply(update, text)

    # ─── /cancel (onboarding fallback) ───

    async def cmd_cancel(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        await self.reply(update, "Onboarding cancelled. Use /start to try again.")
        return ConversationHandler.END

    # ─── Admin Commands ───

    async def cmd_admin_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        if not self.is_admin(chat_id):
            await self.reply(update, "Sorry, this command is for admins only.")
            return

        runner_count = await self.db.get_runner_count()
        recent_runs = await self.db.fetchall(
            "SELECT COUNT(*) as cnt FROM runs WHERE run_date >= date('now', '-7 days')"
        )
        weekly_runs = recent_runs[0]["cnt"] if recent_runs else 0

        text = (
            f"📊 System Status\n\n"
            f"Runners: {runner_count}\n"
            f"Runs this week: {weekly_runs}\n"
            f"Mode: {self.config.bot_mode}\n"
            f"DB: {self.config.coach_db_path}\n"
        )
        await self.reply(update, text)

    async def cmd_admin_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        if not self.is_admin(chat_id):
            await self.reply(update, "Sorry, this command is for admins only.")
            return

        text = (
            "🔧 Admin Commands\n\n"
            "/admin_status - System status\n"
            "/admin_help - Admin command list\n"
            "/admin_reload - Reload knowledge base\n"
            "/admin_backup - Create backup\n"
        )
        await self.reply(update, text)
