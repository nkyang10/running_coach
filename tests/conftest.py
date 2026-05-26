from __future__ import annotations

from datetime import date
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from app.database import Database
from app.models import (
    CoachObservation,
    Injury,
    MetricLog,
    PersonalBest,
    PrimaryGoal,
    Run,
    Runner,
    RunningLevel,
    Shoe,
    ShoeType,
)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[Database, None]:
    database = Database(":memory:")
    await database.connect()
    await database.init_tables()
    yield database
    await database.close()


@pytest.fixture
def sample_runner() -> Runner:
    return Runner(
        chat_id=90001,
        name="Alice",
        age=30,
        gender="female",
        running_level=RunningLevel.BEGINNER,
        primary_goal=PrimaryGoal.IMPROVE_5K,
        current_weekly_km=15,
        last_active=date.today(),
    )


@pytest.fixture
def sample_injury() -> Injury:
    return Injury(
        chat_id=90001,
        body_part="knee",
        injury_type="runners_knee",
        severity="mild",
        description="Mild knee pain after long runs",
        active=True,
    )


@pytest.fixture
def sample_shoe() -> Shoe:
    return Shoe(
        chat_id=90001,
        name="Nike Pegasus 40",
        type=ShoeType.DAILY_TRAINER,
        km_on_shoes=100,
    )


@pytest.fixture
def sample_run() -> Run:
    return Run(
        chat_id=90001,
        run_date=date.today(),
        run_type="easy",
        distance_km=5.0,
        duration_sec=1800,
        avg_pace_sec_per_km=360,
        rpe=5,
    )


@pytest.fixture
def sample_pb() -> PersonalBest:
    return PersonalBest(
        chat_id=90001,
        distance="5k",
        time_sec=1500,
    )


@pytest.fixture
def sample_metric() -> MetricLog:
    return MetricLog(
        chat_id=90001,
        category="body",
        metric_name="weight_kg",
        value=65.0,
        unit="kg",
    )


@pytest.fixture
def sample_observation() -> CoachObservation:
    return CoachObservation(
        chat_id=90001,
        category="motivation",
        observation="Responds well to positive reinforcement",
        evidence="Consistently logs runs after encouraging messages",
        confidence=2,
    )
