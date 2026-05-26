from __future__ import annotations

import time
from collections import defaultdict
from typing import Optional

from aiohttp import web

from app.coach_service import CoachService
from app.config import Config
from app.logger import get_logger

logger = get_logger(__name__)

ONBOARDING_NAME, ONBOARDING_LEVEL, ONBOARDING_GOAL, ONBOARDING_WEEKLY_KM = range(4)


class WhatsAppBot:
    def __init__(self, config: Config, service: CoachService) -> None:
        self.config = config
        self.service = service
        self._last_cmd: dict[str, float] = defaultdict(float)
        self._rate_limit_sec = 1.0
        self._onboard_state: dict[str, dict] = {}
        self._app: Optional[web.Application] = None
        self._twilio_client = None

    def _check_rate_limit(self, user_id: str) -> bool:
        now = time.time()
        if now - self._last_cmd[user_id] < self._rate_limit_sec:
            return False
        self._last_cmd[user_id] = now
        return True

    def is_admin(self, number: str) -> bool:
        return self.service.is_admin(number)

    async def start(self, host: str = "0.0.0.0", port: int = 9000) -> None:
        from twilio.rest import Client

        self._twilio_client = Client(
            self.config.whatsapp_twilio_account_sid,
            self.config.whatsapp_twilio_auth_token,
        )

        app = web.Application()
        app.router.add_post("/whatsapp", self._handle_webhook)
        app.router.add_get("/health", self._handle_health)

        self._app = app
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port, reuse_address=True)
        await site.start()
        logger.info("whatsapp_webhook_started", host=host, port=port)

    async def _handle_health(self, request: web.Request) -> web.Response:
        return web.Response(text="ok")

    async def _handle_webhook(self, request: web.Request) -> web.Response:
        try:
            data = await request.post()
        except Exception:
            data = {}
        from_number = data.get("From", "").replace("whatsapp:", "")
        body = (data.get("Body", "") or "").strip()

        if not from_number:
            return web.Response(text="")

        if from_number in self._onboard_state:
            reply = await self._process_onboarding(from_number, body)
        elif body.startswith("/"):
            reply = await self._handle_command(from_number, body)
        else:
            reply = await self.service.handle_conversation(from_number, body)
            if not reply:
                reply = "Send /help to see available commands."

        if reply:
            await self._send_message(from_number, reply)
        return web.Response(text="")

    async def _send_message(self, to_number: str, text: str) -> None:
        try:
            if self._twilio_client and self.config.whatsapp_from_number:
                self._twilio_client.messages.create(
                    body=text,
                    from_=f"whatsapp:{self.config.whatsapp_from_number}",
                    to=f"whatsapp:{to_number}",
                )
        except Exception as e:
            logger.error("whatsapp_send_failed", to=to_number, error=str(e))

    async def _handle_command(self, from_number: str, text: str) -> str:
        if not self._check_rate_limit(from_number):
            return ""

        parts = text.split()
        cmd = parts[0].lower()
        args = " ".join(parts[1:])

        runner = await self.service.get_or_create_runner(from_number)

        if cmd == "/start":
            if runner:
                return await self.service.get_start_message(from_number)
            self._onboard_state[from_number] = {"step": ONBOARDING_NAME}
            return "Welcome to AI Running Coach! \U0001f3c3\n\nWhat's your name?"

        if cmd == "/help":
            return await self.service.get_help_message()

        if cmd == "/plan":
            return await self.service.get_plan(from_number)

        if cmd == "/log":
            return await self.service.log_run(from_number, args)

        if cmd == "/status":
            return await self.service.get_status(from_number)

        if cmd == "/metrics":
            return await self.service.record_metric(from_number, args)

        if cmd == "/history":
            return await self.service.get_history(from_number)

        if cmd == "/shoes":
            return await self.service.handle_shoes(from_number, args)

        if cmd in (
            "/admin_status",
            "/admin_health",
            "/admin_help",
            "/admin_reload",
            "/admin_backup",
            "/admin_knowledge",
        ):
            return await self._handle_admin_command(from_number, cmd, args)

        return "Unknown command. Use /help."

    async def _handle_admin_command(self, from_number: str, cmd: str, args: str) -> str:
        if not self.is_admin(from_number):
            return "Sorry, this command is for admins only."

        if cmd == "/admin_status":
            return await self.service.get_admin_status()
        if cmd == "/admin_health":
            from admin.system_manager import get_health_report

            return await get_health_report(
                self.service.db, self.service.kb, self.config
            )
        if cmd == "/admin_help":
            return (
                "Admin Commands:\n/admin_status\n/admin_health\n/admin_help\n"
                "/admin_reload\n/admin_backup\n/admin_knowledge"
            )
        if cmd == "/admin_reload":
            return await self.service.admin_reload_kb()
        if cmd == "/admin_backup":
            result = await self.service.admin_backup()
            return result
        if cmd == "/admin_knowledge":
            parts = args.split() if args else []
            return await self.service.admin_knowledge(parts)
        return ""

    async def _process_onboarding(self, from_number: str, text: str) -> str:
        state = self._onboard_state[from_number]
        step = state["step"]

        if step == ONBOARDING_NAME:
            state["name"] = text
            state["step"] = ONBOARDING_LEVEL
            return (
                f"Nice to meet you, {text}!\n\n"
                "What's your running level?\n"
                "1 - New\n2 - Beginner\n3 - Intermediate\n4 - Advanced"
            )

        if step == ONBOARDING_LEVEL:
            if text not in (
                "1",
                "2",
                "3",
                "4",
                "new",
                "beginner",
                "intermediate",
                "advanced",
            ):
                return "Please enter 1, 2, 3, or 4."
            state["level"] = text
            state["step"] = ONBOARDING_GOAL
            return (
                "What's your primary running goal?\n"
                "1 - Finish 5K\n2 - Improve 5K\n"
                "3 - Run 10K\n4 - Half marathon\n"
                "5 - Marathon\n6 - General fitness"
            )

        if step == ONBOARDING_GOAL:
            if text not in ("1", "2", "3", "4", "5", "6"):
                return "Please enter 1-6."
            state["goal"] = text
            state["step"] = ONBOARDING_WEEKLY_KM
            return "How many km do you currently run per week? (0 if just starting)"

        if step == ONBOARDING_WEEKLY_KM:
            try:
                weekly_km = float(text)
            except ValueError:
                return "Please enter a number (e.g., 10 or 0)."

            runner = await self.service.create_runner(
                from_number,
                state.get("name", "Runner"),
                state.get("level", "new"),
                state.get("goal", "general"),
                weekly_km,
            )
            del self._onboard_state[from_number]
            return (
                f"Profile created! \U0001f389\n\n"
                f"Name: {runner.name}\nLevel: {runner.running_level.value}\n"
                f"Goal: {runner.primary_goal.value}\n"
                f"Weekly km: {runner.current_weekly_km}\n\n"
                "Commands: /plan  /log  /status  /metrics  /history  /help"
            )

        return ""
