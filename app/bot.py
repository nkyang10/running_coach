from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from datetime import date
from typing import Optional

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.coach import CoachEngine
from app.config import Config
from app.database import Database
from app.knowledge import KnowledgeBase
from app.logger import get_logger
from app.models import PrimaryGoal, RunningLevel, Runner

logger = get_logger(__name__)

ONBOARDING_NAME, ONBOARDING_LEVEL, ONBOARDING_GOAL, ONBOARDING_WEEKLY_KM = range(4)
PREF_DAYS, PREF_TIME, PREF_VIBE = range(4, 7)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🏃 /plan", "📝 /record", "📊 /status"],
        ["👟 /shoes", "📋 /history", "❓ /help"],
    ],
    resize_keyboard=True,
)


class CoachBot:
    def __init__(
        self,
        config: Config,
        db: Database,
        kb: KnowledgeBase | None = None,
        coach: CoachEngine | None = None,
    ) -> None:
        self.config = config
        self.db = db
        self.kb = kb
        self.coach = coach
        self.application: Optional[Application] = None
        self._last_cmd: dict[int, float] = defaultdict(float)
        self._rate_limit_sec = 1.0

    def _check_rate_limit(self, chat_id: int) -> bool:
        now = time.time()
        if now - self._last_cmd[chat_id] < self._rate_limit_sec:
            return False
        self._last_cmd[chat_id] = now
        return True

    def _sanitize_input(self, text: Optional[str]) -> str:
        if not text:
            return ""
        return text.replace("\x00", "")[:4000]

    async def start_bot(self) -> Application:
        app = Application.builder().token(self.config.telegram_bot_token).build()

        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(CommandHandler("plan", self.cmd_plan))
        app.add_handler(CommandHandler("log", self.cmd_log))
        app.add_handler(CommandHandler("record", self.cmd_log))
        app.add_handler(CommandHandler("status", self.cmd_status))
        app.add_handler(CommandHandler("history", self.cmd_history))
        app.add_handler(CommandHandler("metrics", self.cmd_metrics))
        app.add_handler(CommandHandler("shoes", self.cmd_shoes))
        app.add_handler(CommandHandler("cancel", self.cmd_cancel))

        conv = ConversationHandler(
            entry_points=[CommandHandler("start", self.cmd_start)],
            states={
                ONBOARDING_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._onboard_name)
                ],
                ONBOARDING_LEVEL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._onboard_level)
                ],
                ONBOARDING_GOAL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._onboard_goal)
                ],
                ONBOARDING_WEEKLY_KM: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self._onboard_weekly_km
                    )
                ],
                PREF_DAYS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._pref_days)
                ],
                PREF_TIME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._pref_time)
                ],
                PREF_VIBE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._pref_vibe)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cmd_cancel)],
        )
        app.add_handler(conv)

        self.application = app

        from admin.commands import register_admin_commands

        register_admin_commands(self)

        if self.config.bot_mode == "development":
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            logger.info("bot_started_polling")
        return app

    async def stop_bot(self) -> None:
        if self.application:
            try:
                await self.application.stop()
            except Exception:
                pass
            try:
                await self.application.shutdown()
            except Exception:
                pass
            logger.info("bot_stopped")

    def is_admin(self, chat_id: int) -> bool:
        return chat_id in self.config.admin_chat_ids

    async def reply(self, update: Update, text: str, keyboard=None) -> None:
        if update.message:
            await update.message.reply_text(text)

    # ─── /start ───

    async def cmd_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        chat_id = update.effective_user.id if update.effective_user else 0
        existing = await self.db.get_runner(chat_id)

        if existing:
            msg = (
                f"Hey {existing.name}! 👋 Great to see you again!\n\n"
                f"📊 *Your Status*\n"
                f"Level: `{existing.running_level.value}` | Goal: `{existing.primary_goal.value}`\n"
                f"Streak: {existing.streak_days} days 🔥\n"
                f"Total runs: {existing.total_runs} 🏃\n\n"
                f"Tap a button below or type a command!"
            )
            await self.reply(update, msg, keyboard=MAIN_KEYBOARD)
            return ConversationHandler.END

        context.user_data["onboard_name"] = (
            update.effective_user.first_name if update.effective_user else "Runner"
        )
        await self.reply(
            update,
            f"Hey {context.user_data['onboard_name']}! 👋\n\n"
            f"Let's get to know you a bit so I can be your running buddy 🏃\n\n"
            f"What's your running level?",
            keyboard=ReplyKeyboardMarkup(
                [
                    [
                        "\U0001f331 New (never run)",
                        "\U0001f469\u200d\U0001f3eb Beginner (casual)",
                    ],
                    [
                        "\U0001f3c3\u200d\u2640\ufe0f Intermediate (regular)",
                        "\U0001f525 Advanced (pro)",
                    ],
                ],
                resize_keyboard=True,
            ),
        )
        return ONBOARDING_LEVEL

    async def _onboard_level(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        text = (
            update.message.text.strip()
            if update.message and update.message.text
            else ""
        )
        level_map = {
            "new": RunningLevel.NEW,
            "beginner": RunningLevel.BEGINNER,
            "intermediate": RunningLevel.INTERMEDIATE,
            "advanced": RunningLevel.ADVANCED,
        }
        level = None
        for key, val in level_map.items():
            if key in text.lower():
                level = val
                break
        if not level:
            await self.reply(update, "Pick one of the options above!")
            return ONBOARDING_LEVEL
        context.user_data["onboard_level"] = level

        await self.reply(
            update,
            f"{'Nice!' if level == RunningLevel.NEW else 'Awesome!'} "
            f"Now what's your main running goal?",
            keyboard=ReplyKeyboardMarkup(
                [
                    ["\U0001f3c1 Finish a 5K", "\u23ec Improve my 5K time"],
                    ["\U0001f3c3 Run a 10K", "\U0001f3c0 Half marathon"],
                    ["\U0001f30d Marathon", "\U0001f4aa General fitness"],
                ],
                resize_keyboard=True,
            ),
        )
        return ONBOARDING_GOAL

    async def _onboard_goal(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        text = (
            update.message.text.strip().lower()
            if update.message and update.message.text
            else ""
        )
        goal_map = {
            "5k": PrimaryGoal.FINISH_5K,
            "improve 5k": PrimaryGoal.IMPROVE_5K,
            "10k": PrimaryGoal.IMPROVE_10K,
            "half marathon": PrimaryGoal.HALF_MARATHON,
            "marathon": PrimaryGoal.MARATHON,
            "general": PrimaryGoal.GENERAL,
        }
        goal = None
        for key, val in goal_map.items():
            if key in text:
                goal = val
                break
        if not goal:
            for key, val in goal_map.items():
                if key[0] in text:
                    goal = val
                    break
        if not goal:
            await self.reply(update, "Pick one of the options above!")
            return ONBOARDING_GOAL
        context.user_data["onboard_goal"] = goal

        await self.reply(
            update,
            "Great choice! How many km do you currently run per week?\n"
            "(Type 0 if you're just starting out!)",
        )
        return ONBOARDING_WEEKLY_KM

    async def _onboard_weekly_km(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        try:
            weekly_km = (
                float(update.message.text.strip())
                if update.message and update.message.text
                else 0
            )
        except ValueError:
            await self.reply(update, "Just type a number 🙂 like 10 or 0")
            return ONBOARDING_WEEKLY_KM
        context.user_data["onboard_weekly"] = weekly_km

        await self.reply(
            update,
            "How many days per week can you run?",
            keyboard=ReplyKeyboardMarkup(
                [["1-2 days", "3 days"], ["4 days", "5+ days"]],
                resize_keyboard=True,
            ),
        )
        return PREF_DAYS

    async def _pref_days(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        text = (
            update.message.text.strip()
            if update.message and update.message.text
            else "3"
        )
        days_map = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
        parts = text.split("-")
        if len(parts) >= 2:
            days = int(parts[1].split()[0]) if parts[1].split()[0].isdigit() else 3
        else:
            days = days_map.get(text[0], 3)
        context.user_data["pref_days"] = days

        await self.reply(
            update,
            "What time of day do you usually run?",
            keyboard=ReplyKeyboardMarkup(
                [
                    ["\U0001f305 Morning", "\U0001f318 Lunch"],
                    ["\U0001f307 Evening", "\u2753 No preference"],
                ],
                resize_keyboard=True,
            ),
        )
        return PREF_TIME

    async def _pref_time(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        text = (
            update.message.text.strip().lower()
            if update.message and update.message.text
            else "morning"
        )
        time_map = {"morning": "morning", "lunch": "lunch", "evening": "evening"}
        pref_time = "morning"
        for key, val in time_map.items():
            if key in text:
                pref_time = val
                break
        context.user_data["pref_time"] = pref_time

        await self.reply(
            update,
            "One last thing! What coaching style works for you?",
            keyboard=ReplyKeyboardMarkup(
                [
                    ["\U0001f31f Push me hard!", "\U0001f49a Gentle encouragement"],
                    ["\U0001f4ca Data & details", "\U0001f3af Just the essentials"],
                ],
                resize_keyboard=True,
            ),
        )
        return PREF_VIBE

    async def _pref_vibe(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        text = (
            update.message.text.strip().lower()
            if update.message and update.message.text
            else ""
        )
        vibe = "casual"
        if "push" in text or "hard" in text:
            vibe = "motivational"
        elif "gentle" in text or "encouragement" in text:
            vibe = "gentle"
        elif "data" in text or "detail" in text:
            vibe = "detailed"
        elif "essential" in text:
            vibe = "concise"

        chat_id = update.effective_user.id if update.effective_user else 0
        runner = Runner(
            chat_id=chat_id,
            name=context.user_data.get("onboard_name", "Runner"),
            running_level=context.user_data.get("onboard_level", RunningLevel.NEW),
            primary_goal=context.user_data.get("onboard_goal", PrimaryGoal.GENERAL),
            current_weekly_km=context.user_data.get("onboard_weekly", 0),
            preferred_days=str(context.user_data.get("pref_days", 3)),
            preferred_time=context.user_data.get("pref_time", "morning"),
            communication_style=vibe,
            last_active=date.today(),
        )
        await self.db.create_runner(runner)

        await self.reply(
            update,
            f"You're all set! 🎉\n\n"
            f"Name: {runner.name}\n"
            f"Level: {runner.running_level.value}\n"
            f"Goal: {runner.primary_goal.value}\n"
            f"Weekly: {runner.current_weekly_km}km | {context.user_data.get('pref_days', 3)}x/week\n\n"
            f"Let's get those runs in! 🏃\n"
            f"Hit \U0001f3c3 **/plan** for your first training plan!",
            keyboard=MAIN_KEYBOARD,
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
            "Also available on Discord + WhatsApp.\n"
            "Admin commands available to authorized users."
        )
        await self.reply(update, text)

    # ─── /plan ───

    async def cmd_plan(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        if not self.coach:
            await self.reply(
                update, "Coach is taking a nap \U0001f634 try again later!"
            )
            return

        if not await self.db.get_runner(chat_id):
            await self.reply(
                update, "Let's get to know each other first! Hit /start \U0001f44b"
            )
            return

        thinking_msgs = [
            "\U0001f3c3 Lacing up shoes...",
            "\u2601\ufe0f Checking the weather...",
            "\U0001f50d Consulting the running oracle...",
            "\U0001f4ad Thinking about your goals...",
            "\U0001f3af Fine-tuning the plan...",
            "\u2728 Almost there!",
        ]
        await self.reply(update, thinking_msgs[0])

        async def progress_updater():
            for i in range(1, len(thinking_msgs)):
                await asyncio.sleep(6)
                try:
                    await update.message.reply_text(thinking_msgs[i])
                except Exception:
                    pass

        task = asyncio.create_task(progress_updater())
        try:
            plan = await self.coach.generate_plan(chat_id)
            await self.reply(update, plan, keyboard=MAIN_KEYBOARD)
        finally:
            task.cancel()

    # ─── /log ───

    async def cmd_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        if not await self.db.get_runner(chat_id):
            await self.reply(update, "Please use /start to set up your profile first.")
            return

        text = update.message.text if update.message and update.message.text else ""
        args = text[5:].strip()

        if not args:
            await self.reply(
                update,
                "Please describe your run, e.g.: /log 5k in 25min, felt easy RPE 6",
            )
            return

        if self.coach:
            parsed = await self.coach.parse_run_log(chat_id, args)
        else:
            parsed = {"distance_km": 5, "duration_sec": 1800, "rpe": 5, "notes": args}

        run = (
            await self.coach.save_run_from_parse(chat_id, parsed)
            if self.coach
            else None
        )
        if run:
            dist = run.distance_km or 0
            dur = run.duration_sec or 0
            pace = f"{dur // 60}:{dur % 60:02d} /km" if dist > 0 and dur > 0 else "N/A"
            reply = (
                f"✅ Logged your run!\n"
                f"Distance: {dist:.1f} km\n"
                f"Duration: {dur // 60} min\n"
                f"Pace: {pace}\n"
                f"RPE: {run.rpe or 'N/A'}\n"
                f"Type: {run.run_type or 'N/A'}\n"
                f"Keep up the great work! 🎉"
            )
        else:
            reply = "Run logged successfully! 🎉"
        await self.reply(update, reply)

    # ─── /status ───

    async def cmd_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        runner = await self.db.get_runner(chat_id)
        if not runner:
            await self.reply(update, "Please use /start to set up your profile first.")
            return

        recent = await self.db.get_recent_runs(chat_id, days=30)
        total_km = sum(r.distance_km or 0 for r in recent)
        run_count = len(recent)
        injuries = await self.db.get_injuries(chat_id, active_only=True)

        status = (
            f"📊 *Your Running Status*\n\n"
            f"Level: {runner.running_level.value}\n"
            f"Goal: {runner.primary_goal.value}\n"
            f"Current weekly: {runner.current_weekly_km:.0f} km\n"
            f"Fatigue: {'🟢' if runner.fatigue_level <= 2 else '🟡' if runner.fatigue_level <= 3 else '🔴'} {runner.fatigue_level}/5\n"
            f"Consistency (30d): {runner.consistency_30d:.0%}\n"
            f"Streak: {runner.streak_days} days\n"
            f"Program: {runner.current_program or 'None'}\n"
            f"Week: {runner.week_of_program} | Phase: {runner.training_phase.value}\n"
            f"Total runs: {runner.total_runs}\n\n"
            f"*Last 30 Days*\n"
            f"Runs: {run_count}\n"
            f"Total distance: {total_km:.1f} km\n"
        )

        if injuries:
            status += "\n*Active Injuries*\n"
            for i in injuries:
                status += f"- {i.body_part} ({i.severity})\n"

        status += "\nCommands: /plan  /log  /history  /help"
        await self.reply(update, status)

    # ─── /metrics ───

    async def cmd_metrics(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        if not await self.db.get_runner(chat_id):
            await self.reply(update, "Please use /start to set up your profile first.")
            return

        text = update.message.text if update.message and update.message.text else ""
        args = text[9:].strip()

        if not args:
            recent = await self.db.get_metrics(chat_id, "weight_kg", limit=5)
            if recent:
                lines = ["📏 *Recent Metrics*\n"]
                for m in recent:
                    lines.append(
                        f"- {m.metric_name}: {m.value} {m.unit or ''} ({m.recorded_at})"
                    )
                await self.reply(update, "\n".join(lines))
            else:
                await self.reply(
                    update, "Usage: /metrics <name> <value>  e.g., /metrics weight 72"
                )
            return

        parts = args.split()
        if len(parts) < 2:
            await self.reply(
                update, "Usage: /metrics <name> <value>  e.g., /metrics weight 72"
            )
            return

        name = parts[0].lower()
        try:
            value = float(parts[1])
        except ValueError:
            await self.reply(
                update, "Value must be a number. Usage: /metrics weight 72"
            )
            return

        category_map = {
            "weight": "body",
            "body_weight": "body",
            "weight_kg": "body",
            "sleep": "recovery",
            "sleep_hours": "recovery",
            "resting_hr": "recovery",
            "hrv": "recovery",
            "vo2max": "performance",
            "vo2": "performance",
        }
        cat = category_map.get(name, "body")
        unit_map = {
            "weight": "kg",
            "body_weight": "kg",
            "weight_kg": "kg",
            "sleep_hours": "hours",
            "sleep": "hours",
        }

        from app.models import MetricLog

        metric = MetricLog(
            chat_id=chat_id,
            category=cat,
            metric_name=name,
            value=value,
            unit=unit_map.get(name),
        )
        await self.db.create_metric(metric)
        await self.reply(
            update, f"✅ Recorded {name}: {value} {unit_map.get(name, '')}"
        )

    # ─── /history ───

    async def cmd_history(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        if not await self.db.get_runner(chat_id):
            await self.reply(update, "Please use /start to set up your profile first.")
            return

        runs = await self.db.get_runs(chat_id, limit=10)

        if not runs:
            await self.reply(
                update, "No runs logged yet. Use /log to record your first run!"
            )
            return

        lines = ["📋 *Recent Runs*\n"]
        for i, run in enumerate(runs, 1):
            dist = run.distance_km or 0
            dur = run.duration_sec or 0
            pace = f"{dur // 60}:{dur % 60:02d}" if dur > 0 else "N/A"
            lines.append(
                f"{i}. {run.run_date} | {dist:.1f}km | {dur // 60}min "
                f"({pace}) | {run.run_type or 'run'} | RPE {run.rpe or 'N/A'}"
            )
        lines.append(f"\nTotal: {len(runs)} runs shown. Use /log to add more!")
        await self.reply(update, "\n".join(lines))

    # ─── /shoes ───

    async def cmd_shoes(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        if not await self.db.get_runner(chat_id):
            await self.reply(update, "Please use /start to set up your profile first.")
            return

        from app.models import Shoe as ShoeModel

        text = update.message.text if update.message and update.message.text else ""
        args = text[7:].strip().lower()

        if not args or args == "list":
            shoes = await self.db.get_shoes(chat_id)
            if not shoes:
                await self.reply(
                    update, "No shoes registered. Use:\n/shoes add <name> [type]"
                )
                return
            lines = ["👟 *Your Shoes*\n"]
            for s in shoes:
                retired = " (retired)" if s.retired else ""
                lines.append(f"- {s.name} [{s.type}]: {s.km_on_shoes:.0f}km{retired}")
            await self.reply(update, "\n".join(lines))

        elif args.startswith("add "):
            parts = args[4:].rsplit(" ", 1)
            name = parts[0]
            shoe_type = (
                parts[1]
                if len(parts) > 1
                and parts[1] in ("daily_trainer", "speed", "race", "trail")
                else "daily_trainer"
            )
            shoe = ShoeModel(chat_id=chat_id, name=name, type=shoe_type)
            await self.db.create_shoe(shoe)
            await self.reply(update, f"✅ Added shoe: {name} ({shoe_type})")

        elif args.startswith("retire "):
            name = args[7:].strip()
            shoes = await self.db.get_shoes(chat_id)
            for s in shoes:
                if s.name.lower() == name:
                    s.retired = True
                    await self.db.update_shoe(s)
                    await self.reply(
                        update, f"✅ Retired: {s.name} ({s.km_on_shoes:.0f}km used)"
                    )
                    return
            await self.reply(update, f"Shoe not found: {name}")

        else:
            await self.reply(
                update,
                "Usage:\n/shoes list\n/shoes add <name> [type]\n/shoes retire <name>",
            )

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

        from admin.system_manager import get_system_status

        text = await get_system_status(self.db, self.kb)
        text += f"\n**Mode:** {self.config.bot_mode}"
        text += f"\n**DB:** {self.config.coach_db_path}"
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
            "/admin_health - Full service health report\n"
            "/admin_status - System status\n"
            "/admin_help - Admin command list\n"
            "/admin_reload - Reload knowledge base\n"
            "/admin_backup - Create backup\n"
            "/admin_knowledge - Manage knowledge base\n"
        )
        await self.reply(update, text)

    async def cmd_admin_health(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        if not self.is_admin(chat_id):
            await self.reply(update, "Sorry, this command is for admins only.")
            return
        from admin.system_manager import get_health_report

        report = await get_health_report(self.db, self.kb, self.config)
        await self.reply(update, report)

    async def cmd_admin_reload(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        if not self.is_admin(chat_id):
            await self.reply(update, "Sorry, this command is for admins only.")
            return
        if self.kb:
            self.kb.reload()
            await self.reply(
                update, f"✅ Knowledge base reloaded ({len(self.kb.get_all())} files)."
            )
        else:
            await self.reply(update, "No knowledge base loaded.")

    async def cmd_admin_backup(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        if not self.is_admin(chat_id):
            await self.reply(update, "Sorry, this command is for admins only.")
            return
        from admin.system_manager import create_backup

        await self.reply(update, "📦 Creating backup...")
        path = await create_backup()
        if path:
            await self.reply(update, f"✅ Backup created: {path}")
        else:
            await self.reply(update, "❌ Backup failed.")

    async def cmd_admin_knowledge(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id if update.effective_user else 0
        if not self.is_admin(chat_id):
            await self.reply(update, "Sorry, this command is for admins only.")
            return

        if not self.kb:
            await self.reply(update, "No knowledge base loaded.")
            return

        args = context.args if context.args else []

        if not args:
            files = self.kb.list_files()
            if not files:
                await self.reply(update, "Knowledge base is empty.")
                return
            lines = ["📚 Knowledge Base Files:\n"]
            for f in files:
                lines.append(f"  📄 {f}")
            await self.reply(update, "\n".join(lines))
            return

        subcmd = args[0].lower()

        if subcmd == "show" and len(args) >= 2:
            path = " ".join(args[1:])
            doc = self.kb.get(path)
            if not doc:
                await self.reply(update, f"File not found: {path}")
                return
            content = doc.content
            max_len = 3500
            if len(content) > max_len:
                content = content[:max_len] + "\n\n... (truncated)"
            await self.reply(update, f"📄 *{path}*\n\n{content}")

        elif subcmd == "list":
            files = self.kb.list_files()
            if not files:
                await self.reply(update, "Knowledge base is empty.")
                return
            lines = ["📚 Knowledge Base Files:\n"]
            for f in files:
                lines.append(f"  📄 {f}")
            await self.reply(update, "\n".join(lines))

        elif subcmd == "search" and len(args) >= 2:
            query = " ".join(args[1:])
            results = self.kb.search(query)
            if not results:
                await self.reply(update, f"No results for '{query}'.")
                return
            lines = [f"🔍 Search results for '{query}':\n"]
            for doc in results:
                lines.append(f"  📄 {doc.path} — {doc.title}")
            await self.reply(update, "\n".join(lines))

        elif subcmd == "add" and len(args) >= 3:
            path = args[1]
            content = " ".join(args[2:])
            if self.kb.get(path):
                await self.reply(
                    update, f"File already exists: {path}. Use edit instead."
                )
                return
            self.kb.create(path, content)
            from admin.system_manager import git_commit_knowledge

            await self.reply(update, f"✅ Created: {path}")
            await git_commit_knowledge(f"knowledge/{path}", f"admin: add {path}")

        elif subcmd == "edit" and len(args) >= 3:
            path = args[1]
            content = " ".join(args[2:])
            doc = self.kb.get(path)
            if not doc:
                await self.reply(update, f"File not found: {path}. Use add instead.")
                return
            self.kb.update(path, content)
            from admin.system_manager import git_commit_knowledge

            await self.reply(update, f"✅ Updated: {path}")
            await git_commit_knowledge(f"knowledge/{path}", f"admin: update {path}")

        elif subcmd == "delete" and len(args) >= 2:
            path = " ".join(args[1:])
            if not self.kb.get(path):
                await self.reply(update, f"File not found: {path}")
                return
            self.kb.delete(path)
            from admin.system_manager import git_commit_knowledge

            await self.reply(update, f"✅ Deleted: {path}")
            await git_commit_knowledge(f"knowledge/{path}", f"admin: delete {path}")

        else:
            await self.reply(
                update,
                "Usage:\n/admin_knowledge list\n/admin_knowledge show <path>\n"
                "/admin_knowledge search <query>\n/admin_knowledge add <path> <content>\n"
                "/admin_knowledge edit <path> <content>\n/admin_knowledge delete <path>",
            )
