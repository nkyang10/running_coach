from __future__ import annotations

from typing import Optional

from openai import AsyncOpenAI

from app.config import Config
from app.database import Database
from app.knowledge import KnowledgeBase
from app.logger import get_logger
from app.models import Runner

logger = get_logger(__name__)


class CoachEngine:
    def __init__(self, config: Config, db: Database, kb: KnowledgeBase) -> None:
        self.config = config
        self.db = db
        self.kb = kb
        self.client = AsyncOpenAI(api_key=config.openai_api_key)

    async def generate_plan(self, chat_id: int, weather: Optional[dict] = None) -> str:
        runner = await self.db.get_runner(chat_id)
        if not runner:
            return "Please use /start to set up your profile first."

        philosophy = self.kb.get_content("training-philosophy.md") or ""
        guidelines = self.kb.get_content("admin-guidelines.md") or ""

        program_template = ""
        if runner.current_program:
            program_path = f"programs/{runner.current_program}.md"
            program_template = self.kb.get_content(program_path) or ""

        pace_zones = self.kb.get_content("rules/pace-zones.md") or ""
        progression = self.kb.get_content("rules/progression-rules.md") or ""
        deload_taper = self.kb.get_content("rules/deload-taper.md") or ""
        injury_guide = self.kb.get_content("rules/injury-guide.md") or ""

        recent_runs = await self.db.get_recent_runs(chat_id, days=14)
        injuries = await self.db.get_injuries(chat_id, active_only=True)

        injury_context = ""
        if injuries:
            parts = []
            for inj in injuries:
                parts.append(
                    f"- {inj.body_part} ({inj.severity}): {inj.description or 'No details'}"
                )
            injury_context = "Active injuries:\n" + "\n".join(parts)

        recent_context = ""
        if recent_runs:
            parts = []
            for run in recent_runs[:5]:
                parts.append(
                    f"- {run.run_date}: {run.distance_km or '?'}km, "
                    f"type={run.run_type or '?'}, RPE={run.rpe or '?'}"
                )
            recent_context = "Recent runs:\n" + "\n".join(parts)

        weather_context = ""
        if weather:
            weather_context = (
                f"Weather today: {weather.get('condition', 'unknown')}, "
                f"temp {weather.get('temp_high_c', '?')}C, "
                f"rain {weather.get('rain_mm', 0)}mm, "
                f"wind {weather.get('wind_kmh', 0)}km/h\n"
                f"Weather advice: {weather.get('advice', '')}"
            )

        system_prompt = (
            "You are an expert AI running coach. Generate a personalized training plan "
            "based on the runner's profile, your coaching philosophy, and the rules below.\n\n"
            f"## Coaching Philosophy\n{philosophy}\n\n"
            f"## Admin Guidelines\n{guidelines}\n\n"
            f"## Pace Zones\n{pace_zones}\n\n"
            f"## Progression Rules\n{progression}\n\n"
            f"## Deload & Taper\n{deload_taper}\n\n"
            f"## Injury Guide\n{injury_guide}\n\n"
            f"## Current Program Template\n{program_template}\n\n"
            "## Safety Rules\n"
            "- Maximum 7 sessions per week (including cross-training)\n"
            "- Maximum 2 hard sessions per week (tempo, intervals, race)\n"
            "- Weekly mileage increase: max 10% from previous week\n"
            "- Long run: max 30% of weekly mileage\n"
            "- If injured, modify or substitute exercises that aggravate the injury\n"
            "- Never suggest running through severe pain\n"
            "- Recommend rest day if fatigue >= 4/5\n"
            "- Keep recommendations within the runner's experience level\n"
        )

        user_prompt = self._build_user_prompt(
            runner=runner,
            injury_context=injury_context,
            recent_context=recent_context,
            weather_context=weather_context,
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            plan = (
                response.choices[0].message.content
                or "Sorry, I couldn't generate a plan."
            )
        except Exception as e:
            logger.error("llm_plan_failed", error=str(e))
            plan = self._fallback_plan(runner)

        plan = self._safety_filter(plan, runner)
        return plan

    async def generate_workout_advice(self, chat_id: int, question: str) -> str:
        runner = await self.db.get_runner(chat_id)
        if not runner:
            return "Please use /start to set up your profile first."

        philosophy = self.kb.get_content("training-philosophy.md") or ""
        injury_guide = self.kb.get_content("rules/injury-guide.md") or ""
        pace_zones = self.kb.get_content("rules/pace-zones.md") or ""

        injuries = await self.db.get_injuries(chat_id, active_only=True)
        injury_context = ""
        if injuries:
            parts = [f"- {i.body_part} ({i.severity})" for i in injuries]
            injury_context = "Active injuries:\n" + "\n".join(parts)

        system_prompt = (
            "You are an expert running coach. Answer the runner's question "
            "based on your coaching knowledge. Be concise and practical.\n\n"
            f"## Philosophy\n{philosophy}\n\n"
            f"## Pace Zones\n{pace_zones}\n\n"
            f"## Injury Guide\n{injury_guide}\n\n"
            f"## Runner Context\n"
            f"Level: {runner.running_level.value}\n"
            f"Goal: {runner.primary_goal.value}\n"
            f"Weekly km: {runner.current_weekly_km}\n"
            f"{injury_context}\n"
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0.5,
                max_tokens=1000,
            )
            return (
                response.choices[0].message.content
                or "I'm not sure. Please ask another question."
            )
        except Exception as e:
            logger.error("llm_advice_failed", error=str(e))
            return "I'm having trouble connecting to my AI. Please try again later."

    def _build_user_prompt(
        self,
        runner: Runner,
        injury_context: str,
        recent_context: str,
        weather_context: str,
    ) -> str:
        lines = [
            "## Runner Profile\n",
            f"Name: {runner.name or 'Runner'}",
            f"Level: {runner.running_level.value}",
            f"Goal: {runner.primary_goal.value}",
            f"Current weekly km: {runner.current_weekly_km}",
            f"History: {runner.running_history_months} months",
            f"Preferred days: {runner.preferred_days or 'not set'}",
            f"Preferred time: {runner.preferred_time}",
            f"Max session: {runner.max_session_minutes} min",
            f"Fatigue level: {runner.fatigue_level}/5",
            f"Consistency (30d): {runner.consistency_30d:.0%}",
            f"Streak: {runner.streak_days} days",
            f"Week of program: {runner.week_of_program}",
            f"Training phase: {runner.training_phase.value}",
        ]

        if runner.target_race_name:
            lines.append(f"Target race: {runner.target_race_name}")
            if runner.target_race_date:
                lines.append(f"Race date: {runner.target_race_date}")
        if runner.location_city:
            lines.append(f"Location: {runner.location_city}")

        if injury_context:
            lines.extend(["", injury_context])
        if recent_context:
            lines.extend(["", recent_context])
        if weather_context:
            lines.extend(["", weather_context])

        lines.extend(
            [
                "",
                "Generate a training plan for the next week. Include:",
                "- Daily workout type (easy, tempo, intervals, long run, recovery, cross-train, or rest)",
                "- Specific duration or distance for each workout",
                "- Pace targets or RPE for each workout",
                "- Brief coaching tip for each day",
                "- Notes about warm-up, cool-down, or drills if appropriate",
            ]
        )

        return "\n".join(lines)

    def _safety_filter(self, plan: str, runner: Runner) -> str:
        lines = plan.split("\n")
        warnings = []
        safe_lines = []

        week_km = 0
        hard_sessions = 0
        total_sessions = 0

        for line in lines:
            lower = line.lower()
            km = self._extract_km(line)
            week_km += km

            if any(
                hw in lower for hw in ["tempo", "interval", "race", "track", "speed"]
            ):
                hard_sessions += 1
            if any(
                wt in lower
                for wt in ["run", "workout", "session", "cross-train", "strength"]
            ):
                total_sessions += 1
            if "rest" in lower or "recovery" in lower:
                pass

        max_weekly = runner.current_weekly_km * 1.15
        if week_km > max_weekly and max_weekly > 0:
            warnings.append(
                f"⚠️ Weekly mileage ({week_km:.1f}km) exceeds 115% of current ({max_weekly:.1f}km). Consider reducing."
            )

        if hard_sessions > 2:
            warnings.append(
                f"⚠️ Plan has {hard_sessions} hard sessions. Max recommended is 2 per week."
            )

        if total_sessions > 7:
            warnings.append(
                f"⚠️ Plan has {total_sessions} sessions. Max recommended is 7 per week (including cross-training)."
            )

        if warnings:
            safe_lines.append("📋 *Safety Review*\n")
            safe_lines.extend(warnings)
            safe_lines.append("")
            safe_lines.append("---")
            safe_lines.append("")

        safe_lines.append(plan)
        return "\n".join(safe_lines)

    def _fallback_plan(self, runner: Runner) -> str:
        days_map = {
            3: ["Mon", "Wed", "Fri"],
            4: ["Mon", "Wed", "Fri", "Sat"],
            5: ["Mon", "Tue", "Thu", "Fri", "Sun"],
        }
        default_days = days_map.get(runner.week_of_program % 3 + 3, days_map[4])
        runs = [
            f"**{d}** — Easy run {30 + runner.week_of_program * 2} min @ Zone 2 (conversational pace)"
            for d in default_days
        ]
        runs.append(
            f"**{['Sat','Sun'][default_days[-1]!='Sat']}** — Long run {45 + runner.week_of_program * 5} min @ Zone 2"
        )
        plan = [
            f"🏃 *Weekly Training Plan* — {runner.name or 'Runner'}\n",
            "Here's a basic starting plan while I prepare something more tailored:\n",
            *runs,
            "",
            "💡 *Tips*",
            "- Warm up with 5 min easy jog + dynamic stretches before each run",
            "- Cool down with 5 min easy jog + static stretches after each run",
            "- Listen to your body — take an extra rest day if needed",
        ]
        return "\n".join(plan)

    @staticmethod
    def _extract_km(text: str) -> float:
        import re

        matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:km|k|kilo)", text.lower())
        return sum(float(m) for m in matches) if matches else 0

    @staticmethod
    def _pace_to_seconds(pace_str: str) -> Optional[float]:
        import re

        match = re.match(r"(\d+):(\d+)", pace_str)
        if match:
            return int(match.group(1)) * 60 + int(match.group(2))
        return None
