from __future__ import annotations

import re
from datetime import date
from typing import Any, Optional

import httpx
from openai import AsyncOpenAI

from app.config import Config
from app.database import Database
from app.knowledge import KnowledgeBase
from app.logger import get_logger
from app.models import CoachObservation, Run, Runner

logger = get_logger(__name__)


class CoachEngine:
    def __init__(self, config: Config, db: Database, kb: KnowledgeBase) -> None:
        self.config = config
        self.db = db
        self.kb = kb
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(config.openai_timeout_sec, connect=10.0),
        )
        kwargs = {"api_key": config.openai_api_key, "http_client": http_client}
        if config.openai_base_url:
            kwargs["base_url"] = config.openai_base_url
        self.client = AsyncOpenAI(**kwargs)

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
            "\n"
            "## Output Format\n"
            "Return ONLY valid JSON. Use this structure:\n"
            + (
                '{"plan_name": "Week X", "summary": "...",'
                '"days": [{"day": "Monday", "workout_type": "easy",'
                '"description": "...", "duration_min": 30, "distance_km": null,'
                '"pace_target": "Zone 2", "rpe_target": 4, "coaching_tip": "..."}]}'
            )
            + "\n"
            "Do NOT wrap in markdown code fences. Raw JSON only.\n"
        )

        user_prompt = self._build_user_prompt(
            runner=runner,
            injury_context=injury_context,
            recent_context=recent_context,
            weather_context=weather_context,
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=self.config.openai_max_tokens,
            )
            raw = response.choices[0].message.content or "{}"
        except Exception as e:
            logger.error("llm_plan_failed", error=str(e))
            fallback = self._fallback_plan(runner)
            await self._store_plan(chat_id, fallback)
            return self._format_plan_display(fallback, runner)

        plan_data = self._parse_plan_json(raw)
        plan_data = self._safety_filter_structured(plan_data, runner)
        await self._store_plan(chat_id, plan_data)
        return self._format_plan_display(plan_data, runner)

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
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0.5,
                max_tokens=self.config.openai_max_tokens,
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
                "",
                "Use Telegram Markdown: **bold** for day headers and emphasis.",
                "Use bullet points (`-`) for each day's workout details.",
                "Use `---` as a separator between days. Keep it clean and readable.",
            ]
        )

        return "\n".join(lines)

    def _safety_filter_structured(self, data: dict, runner: Runner) -> dict:
        days = data.get("days", [])
        warnings = []
        week_km = sum(d.get("distance_km") or 0 for d in days)
        hard_sessions = sum(
            1 for d in days if d.get("workout_type") in ("tempo", "interval")
        )
        total_sessions = len(days)

        max_weekly = runner.current_weekly_km * 1.15
        if week_km > max_weekly and max_weekly > 0:
            warnings.append(
                f"Weekly distance {week_km:.0f}km exceeds 115% of current ({max_weekly:.0f}km)"
            )

        if hard_sessions > 2:
            warnings.append(f"Too many hard sessions ({hard_sessions}), max 2")

        if total_sessions > 7:
            warnings.append(f"Too many sessions ({total_sessions}), max 7")

        if warnings:
            data["_warnings"] = warnings
        return data

    def _fallback_plan(self, runner: Runner) -> dict:
        days_map = {
            3: ["Mon", "Wed", "Fri"],
            4: ["Mon", "Wed", "Fri", "Sat"],
            5: ["Mon", "Tue", "Thu", "Fri", "Sun"],
        }
        d = days_map.get(runner.week_of_program % 3 + 3, days_map[4])
        return {
            "plan_name": f"Weekly Plan for {runner.name or 'Runner'}",
            "summary": "Basic starting plan while I prepare something tailored",
            "days": [
                {
                    "day": day,
                    "workout_type": "easy",
                    "description": f"Easy run {30 + runner.week_of_program * 2} min @ Zone 2",
                    "duration_min": 30 + runner.week_of_program * 2,
                    "pace_target": "Zone 2",
                    "rpe_target": 4,
                    "coaching_tip": "Keep conversational pace",
                }
                for day in d
            ]
            + [
                {
                    "day": d[-1] if d[-1] != "Sat" else "Sun",
                    "workout_type": "long_run",
                    "description": f"Long run {45 + runner.week_of_program * 5} min",
                    "duration_min": 45 + runner.week_of_program * 5,
                    "pace_target": "Zone 2",
                    "rpe_target": 4,
                    "coaching_tip": "Fuel properly before and hydrate during",
                }
            ],
        }

    async def _store_plan(self, chat_id: int, plan_data: dict) -> None:
        try:
            import json
            from datetime import date as _d

            all_obs = await self.db.get_observations(chat_id, active_only=True)
            existing = [o for o in all_obs if o.category == "plan"]
            stored = json.dumps(plan_data, ensure_ascii=False)[:2000]
            if existing:
                obs = existing[0]
                obs.observation = stored
                obs.last_observed = _d.today()
            else:
                obs = CoachObservation(
                    chat_id=chat_id,
                    category="plan",
                    observation=stored,
                    evidence="generated",
                    confidence=3,
                    first_observed=_d.today(),
                    last_observed=_d.today(),
                )
                await self.db.create_observation(obs)
        except Exception as e:
            from app.logger import get_logger as _gl

            _gl(__name__).warning("plan_store_failed", error=str(e))

    def _parse_plan_json(self, raw: str) -> dict:
        import json

        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.DOTALL)
        try:
            data = json.loads(raw)
            if "days" in data and isinstance(data["days"], list):
                return data
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("plan_json_parse_failed", error=str(e))
        return {"plan_name": "Weekly Plan", "summary": "", "days": []}

    def _format_plan_display(self, data: dict, runner) -> str:
        name = data.get("plan_name", "Weekly Plan") or "Weekly Plan"
        summary = data.get("summary", "") or ""
        days = data.get("days", [])

        lines = [f"🏃 *{name}*"]
        if summary:
            lines.append(f"_{summary}_\n")

        day_emojis = {
            "easy": "🟢",
            "tempo": "🟡",
            "interval": "🔴",
            "long_run": "🔵",
            "recovery": "💚",
            "cross_train": "💪",
            "rest": "😴",
        }

        for day in days:
            day_name = day.get("day", "?")
            wtype = day.get("workout_type", "run")
            emoji = day_emojis.get(wtype, "🏃")
            desc = day.get("description", "")
            dur = day.get("duration_min")
            dist = day.get("distance_km")
            pace = day.get("pace_target", "")
            rpe = day.get("rpe_target")
            tip = day.get("coaching_tip", "")

            parts = [f"\n{emoji} **{day_name}**"]
            if desc:
                parts.append(f"   {desc}")
            if dur or dist:
                detail = []
                if dur:
                    detail.append(f"{dur} min")
                if dist:
                    detail.append(f"{dist} km")
                if pace:
                    detail.append(f"_{pace}_")
                parts.append(f"   {' | '.join(detail)}")
            if rpe:
                parts.append(f"   RPE target: {rpe}")
            if tip:
                parts.append(f"   💡 {tip}")
            lines.extend(parts)

        week_km = sum(d.get("distance_km") or 0 for d in days)
        week_min = sum(d.get("duration_min") or 0 for d in days)
        if week_km > 0 or week_min > 0:
            lines.append(f"\n📊 **Week Total:** {week_km:.0f} km · {week_min} min")
        lines.append("\n🔥 *Ready to crush this week!*")
        return "\n".join(lines)

    async def parse_run_log(self, chat_id: int, text: str) -> dict[str, Any]:
        prompt = (
            "Parse the following run description and extract structured data. "
            "Return ONLY a JSON object with these fields: "
            "distance_km (float), duration_sec (int), run_type (easy/tempo/interval/long_run/recovery/race/other), "
            "rpe (int 1-10), notes (string). "
            "Set fields to null if not mentioned.\n\n"
            f"Run description: {text}"
        )
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a run log parser. Return ONLY valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=min(1000, self.config.openai_max_tokens),
            )
            content = response.choices[0].message.content or "{}"
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
            import json

            parsed = json.loads(content)
        except Exception as e:
            logger.error("log_parse_failed", error=str(e))
            parsed = self._basic_parse(text)
        return parsed

    async def save_run_from_parse(
        self, chat_id: int, parsed: dict[str, Any]
    ) -> Optional[Run]:
        run = Run(
            chat_id=chat_id,
            run_date=date.today(),
            distance_km=parsed.get("distance_km"),
            duration_sec=parsed.get("duration_sec"),
            run_type=parsed.get("run_type"),
            rpe=parsed.get("rpe"),
            notes=parsed.get("notes"),
            source="manual",
            confidence=0.9,
        )
        created = await self.db.create_run(run)

        runner = await self.db.get_runner(chat_id)
        if runner:
            runner.total_runs = (runner.total_runs or 0) + 1
            runner.last_active = date.today()
            await self.db.update_runner(runner)

        return created

    # ─── Adaptive Engine ───

    async def check_adaptation(self, chat_id: int) -> str:
        runner = await self.db.get_runner(chat_id)
        if not runner:
            return ""

        recent = await self.db.get_recent_runs(chat_id, days=21)
        if len(recent) < 3:
            return ""

        messages = []
        high_rpe_runs = [r for r in recent if r.rpe and r.rpe >= 8]
        low_rpe_runs = [r for r in recent if r.rpe and r.rpe <= 4]
        completed = [r for r in recent if r.distance_km and r.distance_km > 0]
        missed = max(0, (len(recent) // 3) - len(completed))

        if runner.fatigue_level >= 4:
            messages.append(
                "🔴 *High Fatigue Alert*\nYour fatigue level is {}. Consider taking a rest day or easy recovery run.".format(
                    runner.fatigue_level
                )
            )

        if len(high_rpe_runs) >= 3:
            messages.append(
                "🟡 *Intensity Warning*\n{} of your last {} runs were high effort (RPE 8+). Consider swapping a hard day for an easy recovery run.".format(
                    len(high_rpe_runs), len(recent)
                )
            )

        if len(low_rpe_runs) >= 3:
            messages.append(
                "🟢 *Ready for Progression*\nYour recent runs feel easy! Consider slightly increasing distance or adding strides to one session."
            )

        if runner.consistency_30d < 0.5 and runner.total_runs and runner.total_runs > 5:
            messages.append(
                "💪 *Consistency Boost*\nYour 30-day consistency is {:.0%}. Try setting a simple goal: run at least 3 times this week.".format(
                    runner.consistency_30d
                )
            )

        if missed >= 2:
            messages.append(
                "📅 *Missed Sessions*\nYou've missed {} expected sessions recently. Life happens — just get back out there!".format(
                    missed
                )
            )

        deload_msg = await self._check_deload_due(runner, recent)
        if deload_msg:
            messages.append(deload_msg)

        plateau_msg = await self._check_plateau(runner, recent)
        if plateau_msg:
            messages.append(plateau_msg)

        return "\n\n".join(messages) if messages else ""

    async def _check_deload_due(self, runner: Runner, recent: list) -> str:
        if runner.week_of_program >= 4 and runner.week_of_program % 4 == 0:
            return "📋 *Deload Week Suggested*\nYou're entering week {} of your program. Consider a deload week with 40-50% of normal volume and no hard sessions.".format(
                runner.week_of_program
            )
        return ""

    async def _check_plateau(self, runner: Runner, recent: list) -> str:
        if len(recent) < 6:
            return ""

        sorted_runs = sorted(recent, key=lambda r: r.run_date)
        recent_km = [r.distance_km for r in sorted_runs[-6:] if r.distance_km]

        if len(recent_km) < 4:
            return ""

        avg_first3 = sum(recent_km[:3]) / 3
        avg_last3 = sum(recent_km[-3:]) / 3
        diff = avg_last3 - avg_first3

        if abs(diff) < avg_first3 * 0.05 and avg_first3 > 0:
            return "📊 *Possible Plateau*\nYour average distance has been steady at ~{:.1f}km. Try varying your training: add a speed session or extend your long run.".format(
                avg_first3
            )

        if diff < 0 and abs(diff) > avg_first3 * 0.1:
            return "📉 *Declining Trend*\nYour average distance has dropped from {:.1f}km to {:.1f}km. Check in on your motivation or consider a rest week.".format(
                avg_first3, avg_last3
            )

        return ""

    PATTERNS = {
        "injury": [
            (
                r"(?:my\s+)?(shins?|knee|achilles|hip|foot|heel|ankle|back)\s+(hurt|pain|sore|ache)",
                "add_injury",
            ),
            (
                r"(?:i have|got|developed|suffering from)\s+(shin splints|runners? knee|plantar fasciitis|itbs|achilles tendinopathy)",
                "add_injury",
            ),
        ],
        "goal": [
            (
                r"i want to (?:run|finish|complete)\s+(?:a\s+)?(5k|5km|10k|10km|half marathon|marathon)",
                "update_goal",
            ),
            (
                r"i(?:'m|\s+am)\s+(?:training|preparing)\s+for\s+(?:a\s+)?(5k|10k|half marathon|marathon)",
                "update_goal",
            ),
        ],
        "schedule": [
            (r"i can only run (\d+) days?\s+(?:a|per)\s+week", "update_schedule"),
            (
                r"i(?:'m|\s+am)\s+(?:traveling|on vacation|away)\s+(?:next|this)\s+week",
                "note_travel",
            ),
        ],
        "shoe": [
            (r"i got new shoes", "add_shoe"),
            (r"new running shoes", "add_shoe"),
        ],
        "fatigue": [
            (r"legs feel heavy", "note_fatigue"),
            (r"i(?:'m|\s+am)\s+(?:exhausted|so tired|really tired)", "check_recovery"),
        ],
    }

    async def process_conversation(self, chat_id: int, message: str) -> Optional[str]:
        message_lower = message.lower()
        for category, patterns in self.PATTERNS.items():
            for pattern, action in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    if action == "add_injury":
                        body_part = (
                            match.group(1)
                            if match.lastindex and match.lastindex >= 1
                            else match.group(0)
                        )
                        from app.models import Injury as InjuryModel

                        injury = InjuryModel(
                            chat_id=chat_id,
                            body_part=(
                                body_part
                                if body_part
                                in (
                                    "shin",
                                    "knee",
                                    "achilles",
                                    "hip",
                                    "foot",
                                    "heel",
                                    "ankle",
                                    "back",
                                )
                                else "other"
                            ),
                            description=message[:200],
                            source="conversation",
                        )
                        await self.db.create_injury(injury)
                        return f"I've noted your {body_part} issue. Take it easy — listen to your body."

                    elif action == "update_goal":
                        goal_text = match.group(1) if match.lastindex else "5k"
                        goal_map = {
                            "5k": "improve_5k",
                            "5km": "improve_5k",
                            "10k": "10k",
                            "10km": "10k",
                            "half marathon": "half_marathon",
                            "marathon": "marathon",
                        }
                        new_goal = goal_map.get(goal_text, "general")
                        runner = await self.db.get_runner(chat_id)
                        if runner:
                            from app.models import PrimaryGoal

                            runner.primary_goal = PrimaryGoal(new_goal)
                            await self.db.update_runner(runner)
                            return (
                                f"Great goal! I've updated your target to {goal_text}."
                            )

                    elif action == "add_shoe":
                        return "Nice! What brand and model are your new shoes? Use /shoes add <name> [type] to register them."

                    elif action == "note_fatigue":
                        runner = await self.db.get_runner(chat_id)
                        if runner:
                            runner.fatigue_level = min(5, runner.fatigue_level + 1)
                            await self.db.update_runner(runner)
                            return "Sounds like you could use some rest. Consider an easy recovery run or a rest day."

                    elif action == "check_recovery":
                        return "How's your sleep been? Try prioritizing rest and an easy day."

                    elif action == "note_travel":
                        runner = await self.db.get_runner(chat_id)
                        if runner:
                            runner.fatigue_level = min(5, runner.fatigue_level + 1)
                            await self.db.update_runner(runner)
                            return "Travel can disrupt training. Let's plan some easy maintenance runs."

        return None

    async def update_runner_from_adaptation(self, chat_id: int) -> None:
        runner = await self.db.get_runner(chat_id)
        if not runner:
            return

        recent = await self.db.get_recent_runs(chat_id, days=21)
        completed = [r for r in recent if r.distance_km and r.distance_km > 0]

        if len(completed) >= 3:
            avg_rpe = sum(r.rpe or 5 for r in completed) / len(completed)
            if avg_rpe <= 3 and runner.fatigue_level > 1:
                runner.fatigue_level -= 1
            elif avg_rpe >= 7 and runner.fatigue_level < 5:
                runner.fatigue_level += 1

            if runner.consistency_30d is not None:
                current_consistency = min(1.0, len(completed) / max(len(recent), 1))
                runner.consistency_30d = round(current_consistency, 2)

        await self.db.update_runner(runner)

    @staticmethod
    def _basic_parse(text: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "distance_km": None,
            "duration_sec": None,
            "run_type": None,
            "rpe": None,
            "notes": text,
        }

        dist_match = re.search(r"(\d+(?:\.\d+)?)\s*(km|k|kilo|miles|mi)", text.lower())
        if dist_match:
            val = float(dist_match.group(1))
            unit = dist_match.group(2)
            if unit in ("miles", "mi"):
                val *= 1.60934
            result["distance_km"] = round(val, 2)

        dur_match = re.search(r"(\d+)\s*(?:min|mins|minute|minutes)", text.lower())
        if dur_match:
            result["duration_sec"] = int(dur_match.group(1)) * 60

        rpe_match = re.search(r"(?:rpe|effort)\s*[:=]?\s*(\d+)", text.lower())
        if rpe_match:
            result["rpe"] = min(10, max(1, int(rpe_match.group(1))))

        type_map = [
            ("recovery", "recovery"),
            ("easy", "easy"),
            ("tempo", "tempo"),
            ("interval", "interval"),
            ("long", "long_run"),
            ("race", "race"),
            ("speed", "interval"),
            ("hill", "interval"),
            ("track", "interval"),
        ]
        for key, val in type_map:
            if key in text.lower():
                result["run_type"] = val
                break

        return result

    @staticmethod
    def _extract_km(text: str) -> float:
        matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:km|k|kilo)", text.lower())
        return sum(float(m) for m in matches) if matches else 0

    @staticmethod
    def _pace_to_seconds(pace_str: str) -> Optional[float]:
        match = re.match(r"(\d+):(\d+)", pace_str)
        if match:
            return int(match.group(1)) * 60 + int(match.group(2))
        return None
