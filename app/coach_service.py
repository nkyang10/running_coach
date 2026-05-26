from __future__ import annotations

from datetime import date
from typing import Optional

from app.coach import CoachEngine
from app.config import Config
from app.database import Database
from app.knowledge import KnowledgeBase
from app.logger import get_logger
from app.models import MetricLog, PrimaryGoal, Runner, RunningLevel, Shoe

logger = get_logger(__name__)


class CoachService:
    def __init__(
        self, config: Config, db: Database, kb: KnowledgeBase, coach: CoachEngine
    ) -> None:
        self.config = config
        self.db = db
        self.kb = kb
        self.coach = coach

    def is_admin(self, user_id: int | str) -> bool:
        if isinstance(user_id, int):
            return user_id in self.config.admin_chat_ids
        if isinstance(user_id, str):
            return user_id in self.config.whatsapp_admin_numbers
        return False

    async def get_or_create_runner(self, chat_id: int) -> Optional[Runner]:
        return await self.db.get_runner(chat_id)

    async def create_runner(
        self, chat_id: int, name: str, level: str, goal: str, weekly_km: float
    ) -> Runner:
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
        runner = Runner(
            chat_id=chat_id,
            name=name,
            running_level=level_map.get(level.lower(), RunningLevel.NEW),
            primary_goal=goal_map.get(goal.lower(), PrimaryGoal.GENERAL),
            current_weekly_km=weekly_km,
            last_active=date.today(),
        )
        return await self.db.create_runner(runner)

    async def get_start_message(self, chat_id: int) -> str:
        existing = await self.db.get_runner(chat_id)
        if existing:
            return (
                f"Welcome back, {existing.name or 'Runner'}!\n\n"
                f"Current program: {existing.current_program or 'None'}\n"
                f"Week {existing.week_of_program} | Phase: {existing.training_phase}\n"
                f"Total runs: {existing.total_runs}\n"
                f"30-day consistency: {existing.consistency_30d:.0%}\n\n"
                "Commands: /plan  /log  /status  /metrics  /history  /help"
            )
        return "Welcome! Let's get started."

    async def get_help_message(self) -> str:
        return (
            "🤖 AI Running Coach Commands\n\n"
            "/start - View profile or re-onboard\n"
            "/help - Show this message\n"
            "/plan - Generate a personalized training plan\n"
            "/log - Record a run (e.g., '5k in 25min, felt easy')\n"
            "/status - View your progress summary\n"
            "/metrics - Track body metrics (e.g., /metrics weight 72)\n"
            "/history - View recent runs\n"
            "/shoes - Track your shoes\n\n"
            "💬 Just chat with me about your running!\n"
            "Admin commands available to authorized users."
        )

    async def get_plan(self, chat_id: int) -> str:
        runner = await self.db.get_runner(chat_id)
        if not runner:
            return "Please use /start to set up your profile first."
        return await self.coach.generate_plan(chat_id)

    async def log_run(self, chat_id: int, text: str) -> str:
        runner = await self.db.get_runner(chat_id)
        if not runner:
            return "Please use /start to set up your profile first."
        parsed = await self.coach.parse_run_log(chat_id, text)
        run = await self.coach.save_run_from_parse(chat_id, parsed)
        if not run:
            return "Could not save your run. Please try again."
        dist = run.distance_km or 0
        dur = run.duration_sec or 0
        pace = f"{dur // 60}:{dur % 60:02d} /km" if dist > 0 and dur > 0 else "N/A"
        return (
            f"✅ Logged your run!\n"
            f"Distance: {dist:.1f} km\n"
            f"Duration: {dur // 60} min\n"
            f"Pace: {pace}\n"
            f"RPE: {run.rpe or 'N/A'}\n"
            f"Type: {run.run_type or 'N/A'}\n"
            f"Keep up the great work! 🎉"
        )

    async def get_status(self, chat_id: int) -> str:
        runner = await self.db.get_runner(chat_id)
        if not runner:
            return "Please use /start to set up your profile first."
        recent = await self.db.get_recent_runs(chat_id, days=30)
        total_km = sum(r.distance_km or 0 for r in recent)
        run_count = len(recent)
        injuries = await self.db.get_injuries(chat_id, active_only=True)
        lines = [
            "📊 Your Running Status\n",
            f"Level: {runner.running_level.value}",
            f"Goal: {runner.primary_goal.value}",
            f"Current weekly: {runner.current_weekly_km:.0f} km",
            f"Fatigue: {runner.fatigue_level}/5",
            f"Consistency (30d): {runner.consistency_30d:.0%}",
            f"Streak: {runner.streak_days} days",
            f"Program: {runner.current_program or 'None'}",
            f"Week: {runner.week_of_program} | Phase: {runner.training_phase.value}",
            f"Total runs: {runner.total_runs}",
            "",
            "Last 30 Days",
            f"Runs: {run_count}",
            f"Total distance: {total_km:.1f} km",
        ]
        if injuries:
            lines.extend(["", "Active Injuries:"])
            for i in injuries:
                lines.append(f"- {i.body_part} ({i.severity})")
        lines.append("")
        lines.append("Commands: /plan  /log  /history  /help")
        return "\n".join(lines)

    async def record_metric(self, chat_id: int, args: str) -> str:
        if not args:
            recent = await self.db.get_metrics(chat_id, "weight_kg", limit=5)
            if recent:
                lines = ["📏 Recent Metrics:\n"]
                for m in recent:
                    lines.append(f"- {m.metric_name}: {m.value} {m.unit or ''}")
                return "\n".join(lines)
            return "Usage: /metrics <name> <value>  e.g., /metrics weight 72"
        parts = args.split()
        if len(parts) < 2:
            return "Usage: /metrics <name> <value>  e.g., /metrics weight 72"
        name = parts[0].lower()
        try:
            value = float(parts[1])
        except ValueError:
            return "Value must be a number. Usage: /metrics weight 72"
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
        unit_map = {
            "weight": "kg",
            "body_weight": "kg",
            "weight_kg": "kg",
            "sleep_hours": "hours",
        }
        metric = MetricLog(
            chat_id=chat_id,
            category=category_map.get(name, "body"),
            metric_name=name,
            value=value,
            unit=unit_map.get(name),
        )
        await self.db.create_metric(metric)
        return f"✅ Recorded {name}: {value} {unit_map.get(name, '')}"

    async def get_history(self, chat_id: int) -> str:
        runs = await self.db.get_runs(chat_id, limit=10)
        if not runs:
            return "No runs logged yet. Use /log to record your first run!"
        lines = ["📋 Recent Runs:\n"]
        for i, run in enumerate(runs, 1):
            dist = run.distance_km or 0
            dur = run.duration_sec or 0
            pace = f"{dur // 60}:{dur % 60:02d}" if dur > 0 else "N/A"
            lines.append(
                f"{i}. {run.run_date} | {dist:.1f}km | {dur // 60}min "
                f"({pace}) | {run.run_type or 'run'} | RPE {run.rpe or 'N/A'}"
            )
        lines.append(f"\nTotal: {len(runs)} runs shown. Use /log to add more!")
        return "\n".join(lines)

    async def handle_shoes(self, chat_id: int, args: str) -> str:
        if not args or args == "list":
            shoes = await self.db.get_shoes(chat_id)
            if not shoes:
                return "No shoes registered. Use:\n/shoes add <name> [type]"
            lines = ["👟 Your Shoes:\n"]
            for s in shoes:
                retired = " (retired)" if s.retired else ""
                lines.append(f"- {s.name} [{s.type}]: {s.km_on_shoes:.0f}km{retired}")
            return "\n".join(lines)

        if args.startswith("add "):
            rest = args[4:]
            parts = rest.rsplit(" ", 1)
            name = parts[0]
            shoe_type = (
                parts[1]
                if len(parts) > 1
                and parts[1] in ("daily_trainer", "speed", "race", "trail")
                else "daily_trainer"
            )
            shoe = Shoe(chat_id=chat_id, name=name, type=shoe_type)
            await self.db.create_shoe(shoe)
            return f"✅ Added shoe: {name} ({shoe_type})"

        if args.startswith("retire "):
            name = args[7:].strip()
            shoes = await self.db.get_shoes(chat_id)
            for s in shoes:
                if s.name.lower() == name:
                    s.retired = True
                    await self.db.update_shoe(s)
                    return f"✅ Retired: {s.name} ({s.km_on_shoes:.0f}km used)"
            return f"Shoe not found: {name}"

        return "Usage:\n/shoes list\n/shoes add <name> [type]\n/shoes retire <name>"

    async def handle_conversation(self, chat_id: int, message: str) -> Optional[str]:
        return await self.coach.process_conversation(chat_id, message)

    async def get_admin_status(self) -> str:
        from admin.system_manager import get_system_status

        text = await get_system_status(self.db, self.kb)
        text += f"\n**Mode:** {self.config.bot_mode}"
        text += f"\n**DB:** {self.config.coach_db_path}"
        return text

    async def admin_reload_kb(self) -> str:
        if self.kb:
            self.kb.reload()
            return f"✅ Knowledge base reloaded ({len(self.kb.get_all())} files)."
        return "No knowledge base loaded."

    async def admin_backup(self) -> str:
        from admin.system_manager import create_backup

        path = await create_backup()
        if path:
            return f"✅ Backup created: {path}"
        return "❌ Backup failed."

    async def admin_knowledge(self, args: list[str]) -> str:
        if not self.kb:
            return "No knowledge base loaded."
        if not args:
            files = self.kb.list_files()
            if not files:
                return "Knowledge base is empty."
            return "\n".join(
                ["📚 Knowledge Base Files:"] + [f"  📄 {f}" for f in files]
            )

        subcmd = args[0].lower()

        if subcmd == "list":
            files = self.kb.list_files()
            if not files:
                return "Knowledge base is empty."
            return "\n".join(
                ["📚 Knowledge Base Files:"] + [f"  📄 {f}" for f in files]
            )

        if subcmd == "show" and len(args) >= 2:
            path = " ".join(args[1:])
            doc = self.kb.get(path)
            if not doc:
                return f"File not found: {path}"
            content = doc.content
            if len(content) > 3500:
                content = content[:3500] + "\n\n... (truncated)"
            return f"📄 {path}\n\n{content}"

        if subcmd == "search" and len(args) >= 2:
            query = " ".join(args[1:])
            results = self.kb.search(query)
            if not results:
                return f"No results for '{query}'."
            lines = [f"🔍 Search results for '{query}':"]
            for doc in results:
                lines.append(f"  📄 {doc.path} — {doc.title}")
            return "\n".join(lines)

        if subcmd == "add" and len(args) >= 3:
            path = args[1]
            content = " ".join(args[2:])
            if self.kb.get(path):
                return f"File already exists: {path}. Use edit instead."
            self.kb.create(path, content)
            return f"✅ Created: {path}"

        if subcmd == "edit" and len(args) >= 3:
            path = args[1]
            content = " ".join(args[2:])
            if not self.kb.get(path):
                return f"File not found: {path}. Use add instead."
            self.kb.update(path, content)
            return f"✅ Updated: {path}"

        if subcmd == "delete" and len(args) >= 2:
            path = " ".join(args[1:])
            if not self.kb.get(path):
                return f"File not found: {path}"
            self.kb.delete(path)
            return f"✅ Deleted: {path}"

        return (
            "Usage:\n/admin_knowledge list\n/admin_knowledge show <path>\n"
            "/admin_knowledge search <query>\n/admin_knowledge add <path> <content>\n"
            "/admin_knowledge edit <path> <content>\n/admin_knowledge delete <path>"
        )

    async def get_adaptation_message(self, chat_id: int) -> Optional[str]:
        msg = await self.coach.check_adaptation(chat_id)
        return msg if msg else None

    async def update_adaptation(self, chat_id: int) -> None:
        await self.coach.update_runner_from_adaptation(chat_id)
