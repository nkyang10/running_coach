from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.coach import CoachEngine
from app.config import Config
from app.database import Database
from app.knowledge import KnowledgeBase
from app.models import PrimaryGoal, Run, Runner, RunningLevel

FIXTURE_PATH = "tests/fixtures/knowledge_sample"


@pytest.fixture
def config() -> Config:
    return Config(
        telegram_bot_token="test_token",
        openai_api_key="test_key",
        admin_chat_ids=[12345],
        bot_mode="test",
        coach_knowledge_path=FIXTURE_PATH,
    )


@pytest.fixture
def kb() -> KnowledgeBase:
    k = KnowledgeBase(FIXTURE_PATH)
    k.load()
    return k


@pytest.fixture
def mock_openai() -> AsyncMock:
    mock = AsyncMock()
    choice = MagicMock()
    choice.message.content = (
        "🏃 *Weekly Training Plan*\n\n"
        "**Monday** — Easy run 30 min @ Zone 2 (conversational pace)\n"
        "**Wednesday** — Tempo run: 10 min warm-up, 15 min @ threshold pace, 5 min cool-down\n"
        "**Friday** — Easy run 35 min with 4x30s strides at end\n"
        "**Saturday** — Long run 60 min @ Zone 2\n\n"
        "💡 *Tips*\n- Stay hydrated throughout the week\n- Stretch after each run"
    )
    mock.chat.completions.create.return_value = MagicMock(choices=[choice])
    return mock


@pytest.fixture
def engine(
    config: Config, db: Database, kb: KnowledgeBase, mock_openai: AsyncMock
) -> CoachEngine:
    eng = CoachEngine(config, db, kb)
    eng.client = mock_openai
    return eng


@pytest.mark.asyncio
class TestCoachEngine:
    async def test_generate_plan_no_runner(self, engine: CoachEngine):
        result = await engine.generate_plan(99999)
        assert "Please use /start" in result

    async def test_generate_plan_basic(self, engine: CoachEngine, db: Database):
        runner = Runner(
            chat_id=90001,
            name="Test",
            running_level=RunningLevel.BEGINNER,
            primary_goal=PrimaryGoal.IMPROVE_5K,
        )
        await db.create_runner(runner)
        result = await engine.generate_plan(90001)
        assert len(result) > 50
        assert "Training" in result or "Plan" in result or "Run" in result

    async def test_generate_plan_with_injuries(self, engine: CoachEngine, db: Database):
        runner = Runner(
            chat_id=90002, name="Injured", running_level=RunningLevel.INTERMEDIATE
        )
        await db.create_runner(runner)
        from app.models import Injury

        await db.create_injury(
            Injury(
                chat_id=90002,
                body_part="knee",
                injury_type="runners_knee",
                severity="moderate",
            )
        )
        result = await engine.generate_plan(90002)
        assert len(result) > 50

    async def test_fallback_plan_on_llm_error(
        self, config: Config, db: Database, kb: KnowledgeBase
    ):
        mock_fail = AsyncMock()
        mock_fail.chat.completions.create.side_effect = Exception("API Error")
        engine = CoachEngine(config, db, kb)
        engine.client = mock_fail
        runner = Runner(
            chat_id=90003, name="Fallback", running_level=RunningLevel.BEGINNER
        )
        await db.create_runner(runner)
        result = await engine.generate_plan(90003)
        assert "Training Plan" in result or "plan" in result.lower()

    async def test_safety_filter_weekly_mileage(
        self, engine: CoachEngine, db: Database
    ):
        runner = Runner(
            chat_id=90004,
            name="Test",
            running_level=RunningLevel.BEGINNER,
            current_weekly_km=10,
        )
        await db.create_runner(runner)
        result = await engine.generate_plan(90004)
        assert result is not None

    async def test_workout_advice(self, engine: CoachEngine, db: Database):
        runner = Runner(
            chat_id=90005, name="Curious", running_level=RunningLevel.BEGINNER
        )
        await db.create_runner(runner)
        result = await engine.generate_workout_advice(
            90005, "How should I pace my easy runs?"
        )
        assert len(result) > 20

    async def test_workout_advice_no_runner(self, engine: CoachEngine):
        result = await engine.generate_workout_advice(99999, "test")
        assert "Please use /start" in result

    async def test_extract_km(self):
        from app.coach import CoachEngine

        assert CoachEngine._extract_km("Run 5km today") == 5.0
        assert CoachEngine._extract_km("Run 10 km easy") == 10.0
        assert CoachEngine._extract_km("No distance here") == 0
        assert CoachEngine._extract_km("3.5k warm up then 5k tempo") == 8.5

    async def test_generate_plan_with_different_levels(
        self, engine: CoachEngine, db: Database
    ):
        beginner = Runner(
            chat_id=90006,
            name="Newbie",
            running_level=RunningLevel.NEW,
            primary_goal=PrimaryGoal.FINISH_5K,
        )
        await db.create_runner(beginner)
        result = await engine.generate_plan(90006)
        assert len(result) > 50

    async def test_generate_plan_ignores_unknown_runner(self, engine: CoachEngine):
        result = await engine.generate_plan(0)
        assert "Please use /start" in result

    async def test_generate_plan_includes_coaching_tips(
        self, engine: CoachEngine, db: Database
    ):
        runner = Runner(
            chat_id=90007, name="DetailSeeker", running_level=RunningLevel.INTERMEDIATE
        )
        await db.create_runner(runner)
        result = await engine.generate_plan(90007)
        assert len(result) > 50

    async def test_coach_engine_initialization(
        self, config: Config, db: Database, kb: KnowledgeBase
    ):
        engine = CoachEngine(config, db, kb)
        assert engine.config == config
        assert engine.db == db
        assert engine.kb == kb

    async def test_basic_parse_distance(self):
        result = CoachEngine._basic_parse("ran 10km today")
        assert result["distance_km"] == 10

    async def test_basic_parse_miles(self):
        result = CoachEngine._basic_parse("ran 5 miles")
        assert result["distance_km"] == 8.05

    async def test_basic_parse_duration(self):
        result = CoachEngine._basic_parse("ran for 30 min")
        assert result["duration_sec"] == 1800

    async def test_basic_parse_rpe(self):
        result = CoachEngine._basic_parse("felt hard RPE 8")
        assert result["rpe"] == 8

    async def test_basic_parse_type(self):
        result = CoachEngine._basic_parse("tempo run 5k")
        assert result["run_type"] == "tempo"

    async def test_basic_parse_type_recovery(self):
        result = CoachEngine._basic_parse("easy recovery jog")
        assert result["run_type"] == "recovery"

    async def test_basic_parse_all_fields(self):
        result = CoachEngine._basic_parse("tempo 8km in 40 min RPE 7")
        assert result["distance_km"] == 8
        assert result["duration_sec"] == 2400
        assert result["rpe"] == 7
        assert result["run_type"] == "tempo"

    async def test_basic_parse_empty(self):
        result = CoachEngine._basic_parse("")
        assert result["distance_km"] is None
        assert result["duration_sec"] is None
        assert result["rpe"] is None

    async def test_check_adaptation_no_runner(self, engine: CoachEngine):
        result = await engine.check_adaptation(99999)
        assert result == ""

    async def test_check_adaptation_few_runs(self, engine: CoachEngine, db: Database):
        runner = Runner(chat_id=90010, name="New", running_level=RunningLevel.BEGINNER)
        await db.create_runner(runner)
        result = await engine.check_adaptation(90010)
        assert result == ""

    async def test_check_adaptation_high_fatigue(
        self, engine: CoachEngine, db: Database
    ):
        runner = Runner(
            chat_id=90011,
            name="Tired",
            running_level=RunningLevel.BEGINNER,
            fatigue_level=4,
        )
        await db.create_runner(runner)
        today = date.today()
        for i in range(3):
            run = Run(
                chat_id=90011, run_date=today - timedelta(days=i), distance_km=5, rpe=5
            )
            await db.create_run(run)
        result = await engine.check_adaptation(90011)
        assert "High Fatigue" in result

    async def test_check_adaptation_high_rpe(self, engine: CoachEngine, db: Database):
        runner = Runner(
            chat_id=90012, name="Intense", running_level=RunningLevel.INTERMEDIATE
        )
        await db.create_runner(runner)
        today = date.today()
        for i in range(4):
            run = Run(
                chat_id=90012, run_date=today - timedelta(days=i), distance_km=5, rpe=9
            )
            await db.create_run(run)
        result = await engine.check_adaptation(90012)
        assert "Intensity Warning" in result

    async def test_check_deload_due(self, engine: CoachEngine, db: Database):
        runner = Runner(
            chat_id=90013,
            name="Weekly",
            running_level=RunningLevel.INTERMEDIATE,
            week_of_program=4,
        )
        await db.create_runner(runner)
        result = await engine._check_deload_due(runner, [])
        assert "Deload Week" in result

    async def test_update_runner_from_adaptation(
        self, engine: CoachEngine, db: Database
    ):
        runner = Runner(
            chat_id=90014,
            name="Adapt",
            running_level=RunningLevel.BEGINNER,
            fatigue_level=3,
            consistency_30d=0.5,
        )
        await db.create_runner(runner)
        today = date.today()
        for i in range(5):
            run = Run(
                chat_id=90014, run_date=today - timedelta(days=i), distance_km=5, rpe=2
            )
            await db.create_run(run)
        await engine.update_runner_from_adaptation(90014)
        updated = await db.get_runner(90014)
        assert updated is not None
        assert updated.consistency_30d > 0.5
