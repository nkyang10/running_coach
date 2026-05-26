"""Create test runners in the database for development and manual testing."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import date
from app.database import Database
from app.models import Runner, Injury, RunningLevel, PrimaryGoal

TEST_RUNNERS = [
    {
        "runner": Runner(
            chat_id=90001,
            name="Alice (Beginner 5K)",
            running_level=RunningLevel.BEGINNER,
            primary_goal=PrimaryGoal.FINISH_5K,
            current_weekly_km=10,
            running_history_months=2,
            fatigue_level=3,
            consistency_30d=0.7,
            streak_days=5,
            total_runs=8,
            last_active=date.today(),
        ),
        "injuries": [],
    },
    {
        "runner": Runner(
            chat_id=90002,
            name="Bob (10K Improver)",
            running_level=RunningLevel.INTERMEDIATE,
            primary_goal=PrimaryGoal.IMPROVE_10K,
            current_weekly_km=30,
            running_history_months=12,
            fatigue_level=4,
            consistency_30d=0.85,
            streak_days=14,
            total_runs=60,
            last_active=date.today(),
        ),
        "injuries": [
            Injury(
                chat_id=90002,
                body_part="shoulder",
                injury_type="impingement",
                severity="mild",
                description="Mild shoulder impingement",
                active=True,
            ),
        ],
    },
    {
        "runner": Runner(
            chat_id=90003,
            name="Charlie (Half Marathon)",
            running_level=RunningLevel.ADVANCED,
            primary_goal=PrimaryGoal.HALF_MARATHON,
            current_weekly_km=50,
            running_history_months=36,
            fatigue_level=2,
            consistency_30d=0.9,
            streak_days=30,
            total_runs=200,
            last_active=date.today(),
            target_race_name="City Half Marathon",
            target_race_date=date(2026, 12, 1),
            target_race_time_sec=5400,
            location_city="Hong Kong",
        ),
        "injuries": [],
    },
    {
        "runner": Runner(
            chat_id=90004,
            name="Diana (Injured)",
            running_level=RunningLevel.BEGINNER,
            primary_goal=PrimaryGoal.GENERAL,
            current_weekly_km=15,
            running_history_months=6,
            fatigue_level=5,
            consistency_30d=0.4,
            streak_days=2,
            total_runs=15,
            last_active=date.today(),
        ),
        "injuries": [
            Injury(
                chat_id=90004,
                body_part="knee",
                injury_type="runners_knee",
                severity="moderate",
                description="Patellar tendinitis after long runs",
                active=True,
            ),
            Injury(
                chat_id=90004,
                body_part="shin",
                injury_type="shin_splints",
                severity="mild",
                description="Shin pain when increasing mileage",
                active=True,
            ),
        ],
    },
    {
        "runner": Runner(
            chat_id=90005,
            name="Eve (New Runner)",
            running_level=RunningLevel.NEW,
            primary_goal=PrimaryGoal.FINISH_5K,
            current_weekly_km=0,
            running_history_months=0,
            fatigue_level=2,
            consistency_30d=0,
            streak_days=0,
            total_runs=0,
            last_active=date.today(),
        ),
        "injuries": [],
    },
]


async def seed():
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "coach.db"
    )
    db = Database(db_path)
    await db.connect()
    await db.init_tables()

    created = 0
    for entry in TEST_RUNNERS:
        runner = entry["runner"]
        existing = await db.get_runner(runner.chat_id)
        if existing:
            print(f"  ⚠️  Runner {runner.chat_id} already exists — skipping")
            continue
        await db.create_runner(runner)
        print(f"  ✅ Created: {runner.name} (chat_id={runner.chat_id})")
        for injury in entry["injuries"]:
            await db.create_injury(injury)
            print(f"     Added injury: {injury.body_part}")
        created += 1

    await db.close()
    print(f"\n✅ {created} test runners created in {db_path}")


if __name__ == "__main__":
    asyncio.run(seed())
