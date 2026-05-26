"""
Create test users in the database for development and manual testing.

⚠️  Requires Phase 1 (app.database must exist).
    Only run after completing Phase 1 core infrastructure.

Run: python scripts/create_test_users.py

This populates the database with 5 test users of varying profiles
so you can manually test the bot without onboarding real users.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import aiosqlite
from app.database import create_user, create_injury, init_tables

TEST_USERS = [
    {
        "chat_id": 90001,
        "name": "Alice (Beginner)",
        "level": "beginner",
        "goal": "strength",
        "experience_years": 0.5,
        "sessions_per_week": 3,
        "equipment": ["barbell", "squat_rack"],
        "injuries": [],
    },
    {
        "chat_id": 90002,
        "name": "Bob (Intermediate)",
        "level": "intermediate",
        "goal": "hypertrophy",
        "experience_years": 2.0,
        "sessions_per_week": 4,
        "equipment": ["barbell", "squat_rack", "dumbbells", "cables"],
        "injuries": [
            {"body_part": "shoulder", "description": "Mild impingement",
             "severity": "mild", "active": True},
        ],
    },
    {
        "chat_id": 90003,
        "name": "Charlie (Advanced)",
        "level": "advanced",
        "goal": "strength",
        "experience_years": 5.0,
        "sessions_per_week": 5,
        "equipment": ["barbell", "squat_rack", "dumbbells", "bands", "platform"],
        "injuries": [],
    },
    {
        "chat_id": 90004,
        "name": "Diana (Injured)",
        "level": "intermediate",
        "goal": "general",
        "experience_years": 3.0,
        "sessions_per_week": 3,
        "equipment": ["barbell", "dumbbells"],
        "injuries": [
            {"body_part": "lower_back", "description": "Disc bulge",
             "severity": "moderate", "active": True},
            {"body_part": "knee", "description": "Patellar tendinitis",
             "severity": "mild", "active": True},
        ],
    },
    {
        "chat_id": 90005,
        "name": "Eve (Minimal Equipment)",
        "level": "beginner",
        "goal": "fat_loss",
        "experience_years": 0.0,
        "sessions_per_week": 4,
        "equipment": ["dumbbells_5-20", "resistance_bands"],
        "injuries": [],
    },
]


async def seed():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data", "coach.db")

    # Ensure data dir exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        await init_tables(db)

        for user_data in TEST_USERS:
            injuries = user_data.pop("injuries", [])
            equipment = user_data.pop("equipment", [])

            try:
                await create_user(db, **user_data)
                print(f"  ✅ Created user: {user_data['name']} ({user_data['chat_id']})")
            except Exception as e:
                print(f"  ⚠️  User {user_data['chat_id']} already exists: {e}")
                continue

            for injury in injuries:
                await create_injury(db, chat_id=user_data["chat_id"], **injury)
                print(f"     Added injury: {injury['body_part']} ({injury['severity']})")

            for item in equipment:
                await db.execute(
                    "INSERT OR IGNORE INTO equipment (chat_id, item) VALUES (?, ?)",
                    (user_data["chat_id"], item)
                )
            await db.commit()

    print(f"\n✅ {len(TEST_USERS)} test users created in {db_path}")
    print("   You can now interact with the bot using these chat IDs.")


if __name__ == "__main__":
    asyncio.run(seed())
