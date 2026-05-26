from __future__ import annotations

import time
from collections import defaultdict
from typing import Optional

import discord
from discord.ext import commands

from app.coach_service import CoachService
from app.config import Config
from app.logger import get_logger

logger = get_logger(__name__)

ONBOARDING_NAME, ONBOARDING_LEVEL, ONBOARDING_GOAL, ONBOARDING_WEEKLY_KM = range(4)


class DiscordBot:
    def __init__(self, config: Config, service: CoachService) -> None:
        self.config = config
        self.service = service
        self._last_cmd: dict[int, float] = defaultdict(float)
        self._rate_limit_sec = 1.0
        self._onboard_state: dict[int, dict] = {}
        self.bot: Optional[commands.Bot] = None

    def _check_rate_limit(self, user_id: int) -> bool:
        now = time.time()
        if now - self._last_cmd[user_id] < self._rate_limit_sec:
            return False
        self._last_cmd[user_id] = now
        return True

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.config.admin_chat_ids

    intents = discord.Intents.default()
    intents.message_content = True

    async def start(self, token: str) -> None:
        bot = commands.Bot(command_prefix="/", intents=self.intents)

        @bot.event
        async def on_ready():
            logger.info("discord_bot_ready", user=str(bot.user))

        @bot.command(name="start")
        async def cmd_start(ctx: commands.Context):
            if not self._check_rate_limit(ctx.author.id):
                return
            existing = await self.service.get_or_create_runner(ctx.author.id)
            if existing:
                await ctx.reply(await self.service.get_start_message(ctx.author.id))
            else:
                self._onboard_state[ctx.author.id] = {"step": ONBOARDING_NAME}
                await ctx.reply("Welcome to AI Running Coach! 🏃\n\nWhat's your name?")

        @bot.command(name="help")
        async def cmd_help(ctx: commands.Context):
            if not self._check_rate_limit(ctx.author.id):
                return
            msg = await self.service.get_help_message()
            msg += "\nAlso available on Telegram + WhatsApp."
            await ctx.reply(msg)

        @bot.command(name="plan")
        async def cmd_plan(ctx: commands.Context):
            if not self._check_rate_limit(ctx.author.id):
                return
            await ctx.reply("🏃 Generating your personalized training plan...")
            plan = await self.service.get_plan(ctx.author.id)
            await ctx.reply(plan)

        @bot.command(name="log")
        async def cmd_log(ctx: commands.Context, *, args: str = ""):
            if not self._check_rate_limit(ctx.author.id):
                return
            reply = await self.service.log_run(ctx.author.id, args)
            await ctx.reply(reply)

        @bot.command(name="status")
        async def cmd_status(ctx: commands.Context):
            if not self._check_rate_limit(ctx.author.id):
                return
            await ctx.reply(await self.service.get_status(ctx.author.id))

        @bot.command(name="metrics")
        async def cmd_metrics(ctx: commands.Context, *, args: str = ""):
            if not self._check_rate_limit(ctx.author.id):
                return
            await ctx.reply(await self.service.record_metric(ctx.author.id, args))

        @bot.command(name="history")
        async def cmd_history(ctx: commands.Context):
            if not self._check_rate_limit(ctx.author.id):
                return
            await ctx.reply(await self.service.get_history(ctx.author.id))

        @bot.command(name="admin_status")
        async def cmd_admin_status(ctx: commands.Context):
            if not self.is_admin(ctx.author.id):
                await ctx.reply("Sorry, this command is for admins only.")
                return
            await ctx.reply(await self.service.get_admin_status())

        @bot.command(name="admin_health")
        async def cmd_admin_health(ctx: commands.Context):
            if not self.is_admin(ctx.author.id):
                await ctx.reply("Sorry, this command is for admins only.")
                return
            from admin.system_manager import get_health_report

            report = await get_health_report(
                self.service.db, self.service.kb, self.config
            )
            await ctx.reply(report)

        @bot.command(name="admin_help")
        async def cmd_admin_help(ctx: commands.Context):
            if not self.is_admin(ctx.author.id):
                await ctx.reply("Sorry, this command is for admins only.")
                return
            await ctx.reply(
                "🔧 Admin Commands\n\n"
                "/admin_status - System status\n"
                "/admin_help - Admin command list\n"
                "/admin_reload - Reload knowledge base\n"
                "/admin_backup - Create backup\n"
                "/admin_knowledge - Manage knowledge base"
            )

        @bot.command(name="admin_reload")
        async def cmd_admin_reload(ctx: commands.Context):
            if not self.is_admin(ctx.author.id):
                await ctx.reply("Sorry, this command is for admins only.")
                return
            await ctx.reply(await self.service.admin_reload_kb())

        @bot.command(name="admin_backup")
        async def cmd_admin_backup(ctx: commands.Context):
            if not self.is_admin(ctx.author.id):
                await ctx.reply("Sorry, this command is for admins only.")
                return
            await ctx.reply("📦 Creating backup...")
            await ctx.reply(await self.service.admin_backup())

        @bot.command(name="admin_knowledge")
        async def cmd_admin_knowledge(ctx: commands.Context, *, args: str = ""):
            if not self.is_admin(ctx.author.id):
                await ctx.reply("Sorry, this command is for admins only.")
                return
            parts = args.split() if args else []
            await ctx.reply(await self.service.admin_knowledge(parts))

        @bot.event
        async def on_message(message: discord.Message):
            if message.author.bot:
                return

            if message.content.startswith("/"):
                await bot.process_commands(message)
                return

            user_id = message.author.id
            if user_id in self._onboard_state:
                state = self._onboard_state[user_id]
                step = state["step"]

                if step == ONBOARDING_NAME:
                    state["name"] = message.content.strip()
                    state["step"] = ONBOARDING_LEVEL
                    await message.channel.send(
                        f"Nice to meet you, {state['name']}!\n\n"
                        "What's your running level?\n"
                        "1 - New\n2 - Beginner\n3 - Intermediate\n4 - Advanced"
                    )

                elif step == ONBOARDING_LEVEL:
                    level = message.content.strip()
                    if level not in (
                        "1",
                        "2",
                        "3",
                        "4",
                        "new",
                        "beginner",
                        "intermediate",
                        "advanced",
                    ):
                        await message.channel.send("Please enter 1, 2, 3, or 4.")
                        return
                    state["level"] = level
                    state["step"] = ONBOARDING_GOAL
                    await message.channel.send(
                        "What's your primary running goal?\n"
                        "1 - Finish 5K\n2 - Improve 5K\n"
                        "3 - Run 10K\n4 - Half marathon\n"
                        "5 - Marathon\n6 - General fitness"
                    )

                elif step == ONBOARDING_GOAL:
                    goal = message.content.strip()
                    if goal not in ("1", "2", "3", "4", "5", "6"):
                        await message.channel.send("Please enter 1-6.")
                        return
                    state["goal"] = goal
                    state["step"] = ONBOARDING_WEEKLY_KM
                    await message.channel.send(
                        "How many km do you currently run per week? (0 if just starting)"
                    )

                elif step == ONBOARDING_WEEKLY_KM:
                    try:
                        weekly_km = float(message.content.strip())
                    except ValueError:
                        await message.channel.send(
                            "Please enter a number (e.g., 10 or 0)."
                        )
                        return

                    runner = await self.service.create_runner(
                        user_id,
                        state.get("name", "Runner"),
                        state.get("level", "new"),
                        state.get("goal", "general"),
                        weekly_km,
                    )
                    del self._onboard_state[user_id]
                    await message.channel.send(
                        f"Profile created! 🎉\n\n"
                        f"Name: {runner.name}\nLevel: {runner.running_level.value}\n"
                        f"Goal: {runner.primary_goal.value}\n"
                        f"Weekly km: {runner.current_weekly_km}\n\n"
                        "Commands: /plan  /log  /status  /metrics  /history  /help"
                    )
                return

            reply = await self.service.handle_conversation(user_id, message.content)
            if reply:
                await message.channel.send(reply)

        self.bot = bot
        await bot.start(token)
