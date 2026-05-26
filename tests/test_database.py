from __future__ import annotations

from datetime import date

import pytest

from app.models import (
    CoachObservation,
    Injury,
    Milestone,
    PersonalBest,
    Run,
    Runner,
    RunSplit,
    Shoe,
)


@pytest.mark.asyncio
class TestRunnerCRUD:
    async def test_create_runner(self, db, sample_runner):
        result = await db.create_runner(sample_runner)
        assert result.chat_id == 90001
        assert result.name == "Alice"
        assert result.created_at is not None

    async def test_get_runner_exists(self, db, sample_runner):
        await db.create_runner(sample_runner)
        fetched = await db.get_runner(90001)
        assert fetched is not None
        assert fetched.name == "Alice"
        assert fetched.chat_id == 90001

    async def test_get_runner_not_found(self, db):
        fetched = await db.get_runner(99999)
        assert fetched is None

    async def test_update_runner(self, db, sample_runner):
        await db.create_runner(sample_runner)
        sample_runner.name = "Alice Updated"
        sample_runner.fatigue_level = 4
        updated = await db.update_runner(sample_runner)
        assert updated.name == "Alice Updated"
        assert updated.fatigue_level == 4
        assert updated.updated_at is not None

    async def test_delete_runner(self, db, sample_runner):
        await db.create_runner(sample_runner)
        deleted = await db.delete_runner(90001)
        assert deleted is True
        assert await db.get_runner(90001) is None

    async def test_delete_runner_not_found(self, db):
        deleted = await db.delete_runner(99999)
        assert deleted is False

    async def test_get_all_runners(self, db):
        r1 = Runner(chat_id=1001, name="Alice")
        r2 = Runner(chat_id=1002, name="Bob")
        await db.create_runner(r1)
        await db.create_runner(r2)
        runners = await db.get_all_runners()
        assert len(runners) >= 2

    async def test_get_runner_count(self, db):
        await db.create_runner(Runner(chat_id=2001))
        await db.create_runner(Runner(chat_id=2002))
        await db.create_runner(Runner(chat_id=2003))
        count = await db.get_runner_count()
        assert count >= 3

    async def test_runner_with_optional_fields(self, db):
        runner = Runner(
            chat_id=3001,
            name="Charlie",
            age=25,
            gender="male",
            running_level="advanced",
            primary_goal="marathon",
            target_race_name="Boston Marathon",
            current_weekly_km=80,
            location_city="Boston",
            weather_enabled=True,
        )
        await db.create_runner(runner)
        fetched = await db.get_runner(3001)
        assert fetched is not None
        assert fetched.age == 25
        assert fetched.running_level == "advanced"
        assert fetched.primary_goal == "marathon"
        assert fetched.location_city == "Boston"
        assert fetched.weather_enabled is True


@pytest.mark.asyncio
class TestInjuryCRUD:
    async def test_create_injury(self, db, sample_runner, sample_injury):
        await db.create_runner(sample_runner)
        result = await db.create_injury(sample_injury)
        assert result.id is not None
        assert result.body_part == "knee"

    async def test_get_active_injuries(self, db, sample_runner, sample_injury):
        await db.create_runner(sample_runner)
        await db.create_injury(sample_injury)
        injuries = await db.get_injuries(90001, active_only=True)
        assert len(injuries) == 1
        assert injuries[0].body_part == "knee"

    async def test_get_all_injuries(self, db, sample_runner):
        await db.create_runner(sample_runner)
        i1 = Injury(chat_id=90001, body_part="knee", active=True)
        i2 = Injury(chat_id=90001, body_part="shin", active=False)
        await db.create_injury(i1)
        await db.create_injury(i2)
        all_injuries = await db.get_injuries(90001, active_only=False)
        assert len(all_injuries) == 2

    async def test_update_injury(self, db, sample_runner, sample_injury):
        await db.create_runner(sample_runner)
        created = await db.create_injury(sample_injury)
        created.active = False
        updated = await db.update_injury(created)
        assert updated.active is False

    async def test_empty_injuries(self, db):
        injuries = await db.get_injuries(99999)
        assert injuries == []


@pytest.mark.asyncio
class TestShoeCRUD:
    async def test_create_shoe(self, db, sample_runner, sample_shoe):
        await db.create_runner(sample_runner)
        result = await db.create_shoe(sample_shoe)
        assert result.id is not None
        assert result.name == "Nike Pegasus 40"

    async def test_get_active_shoes(self, db, sample_runner, sample_shoe):
        await db.create_runner(sample_runner)
        await db.create_shoe(sample_shoe)
        shoes = await db.get_shoes(90001, active_only=True)
        assert len(shoes) == 1

    async def test_retired_shoe_excluded(self, db, sample_runner):
        await db.create_runner(sample_runner)
        s1 = Shoe(chat_id=90001, name="Shoe 1", retired=False)
        s2 = Shoe(chat_id=90001, name="Shoe 2", retired=True)
        await db.create_shoe(s1)
        await db.create_shoe(s2)
        active = await db.get_shoes(90001, active_only=True)
        assert len(active) == 1
        assert active[0].name == "Shoe 1"

    async def test_update_shoe_mileage(self, db, sample_runner, sample_shoe):
        await db.create_runner(sample_runner)
        created = await db.create_shoe(sample_shoe)
        created.km_on_shoes = 250
        updated = await db.update_shoe(created)
        assert updated.km_on_shoes == 250

    async def test_empty_shoes(self, db):
        shoes = await db.get_shoes(99999)
        assert shoes == []


@pytest.mark.asyncio
class TestRunCRUD:
    async def test_create_run(self, db, sample_runner, sample_run):
        await db.create_runner(sample_runner)
        result = await db.create_run(sample_run)
        assert result.id is not None

    async def test_get_runs(self, db, sample_runner, sample_run):
        await db.create_runner(sample_runner)
        await db.create_run(sample_run)
        runs = await db.get_runs(90001)
        assert len(runs) == 1

    async def test_get_run_by_id(self, db, sample_runner, sample_run):
        await db.create_runner(sample_runner)
        created = await db.create_run(sample_run)
        fetched = await db.get_run(created.id)
        assert fetched is not None
        assert fetched.distance_km == 5.0

    async def test_get_run_not_found(self, db):
        fetched = await db.get_run(99999)
        assert fetched is None

    async def test_get_recent_runs(self, db, sample_runner):
        await db.create_runner(sample_runner)
        from datetime import timedelta

        old_run = Run(
            chat_id=90001, run_date=date.today() - timedelta(days=60), distance_km=3
        )
        new_run = Run(chat_id=90001, run_date=date.today(), distance_km=5)
        await db.create_run(old_run)
        await db.create_run(new_run)
        recent = await db.get_recent_runs(90001, days=30)
        assert len(recent) == 1
        assert recent[0].distance_km == 5

    async def test_get_runs_pagination(self, db, sample_runner):
        await db.create_runner(sample_runner)
        for i in range(5):
            await db.create_run(
                Run(chat_id=90001, run_date=date.today(), distance_km=float(i))
            )
        runs_page = await db.get_runs(90001, limit=2)
        assert len(runs_page) == 2


@pytest.mark.asyncio
class TestRunSplitCRUD:
    async def test_create_split(self, db, sample_runner, sample_run):
        await db.create_runner(sample_runner)
        run = await db.create_run(sample_run)
        split = RunSplit(run_id=run.id, split_number=1, distance_m=400, duration_sec=90)
        result = await db.create_run_split(split)
        assert result.id is not None

    async def test_get_splits(self, db, sample_runner, sample_run):
        await db.create_runner(sample_runner)
        run = await db.create_run(sample_run)
        for i in range(4):
            await db.create_run_split(
                RunSplit(
                    run_id=run.id, split_number=i + 1, distance_m=400, duration_sec=90
                )
            )
        splits = await db.get_run_splits(run.id)
        assert len(splits) == 4


@pytest.mark.asyncio
class TestPersonalBestCRUD:
    async def test_upsert_new_pb(self, db, sample_runner, sample_pb):
        await db.create_runner(sample_runner)
        result = await db.upsert_personal_best(sample_pb)
        assert result.id is not None

    async def test_upsert_existing_pb(self, db, sample_runner, sample_pb):
        await db.create_runner(sample_runner)
        await db.upsert_personal_best(sample_pb)
        sample_pb.time_sec = 1400
        await db.upsert_personal_best(sample_pb)
        pbs = await db.get_personal_bests(90001)
        assert len(pbs) == 1
        assert pbs[0].time_sec == 1400

    async def test_get_personal_bests(self, db, sample_runner):
        await db.create_runner(sample_runner)
        await db.upsert_personal_best(
            PersonalBest(chat_id=90001, distance="5k", time_sec=1500)
        )
        await db.upsert_personal_best(
            PersonalBest(chat_id=90001, distance="10k", time_sec=3200)
        )
        pbs = await db.get_personal_bests(90001)
        assert len(pbs) == 2


@pytest.mark.asyncio
class TestMetricLogCRUD:
    async def test_create_metric(self, db, sample_runner, sample_metric):
        await db.create_runner(sample_runner)
        result = await db.create_metric(sample_metric)
        assert result.id is not None

    async def test_get_metrics(self, db, sample_runner, sample_metric):
        await db.create_runner(sample_runner)
        await db.create_metric(sample_metric)
        metrics = await db.get_metrics(90001, "weight_kg")
        assert len(metrics) == 1
        assert metrics[0].value == 65.0


@pytest.mark.asyncio
class TestObservationCRUD:
    async def test_create_observation(self, db, sample_runner, sample_observation):
        await db.create_runner(sample_runner)
        result = await db.create_observation(sample_observation)
        assert result.id is not None
        assert result.first_observed is not None
        assert result.last_observed is not None

    async def test_get_active_observations(self, db, sample_runner):
        await db.create_runner(sample_runner)
        obs1 = CoachObservation(
            chat_id=90001,
            category="pattern",
            observation="Skips long runs",
            active=True,
        )
        obs2 = CoachObservation(
            chat_id=90001,
            category="preference",
            observation="Likes morning runs",
            active=False,
        )
        await db.create_observation(obs1)
        await db.create_observation(obs2)
        active = await db.get_observations(90001, active_only=True)
        assert len(active) == 1


@pytest.mark.asyncio
class TestTagsCRUD:
    async def test_add_tag(self, db, sample_runner):
        await db.create_runner(sample_runner)
        await db.add_tag(90001, "morning_runner")
        tags = await db.get_tags(90001)
        assert "morning_runner" in tags

    async def test_add_duplicate_tag(self, db, sample_runner):
        await db.create_runner(sample_runner)
        await db.add_tag(90001, "test_tag")
        await db.add_tag(90001, "test_tag")
        tags = await db.get_tags(90001)
        assert len(tags) == 1

    async def test_remove_tag(self, db, sample_runner):
        await db.create_runner(sample_runner)
        await db.add_tag(90001, "temp_tag")
        await db.remove_tag(90001, "temp_tag")
        tags = await db.get_tags(90001)
        assert "temp_tag" not in tags

    async def test_empty_tags(self, db):
        tags = await db.get_tags(99999)
        assert tags == []


@pytest.mark.asyncio
class TestMilestoneCRUD:
    async def test_create_milestone(self, db, sample_runner):
        await db.create_runner(sample_runner)
        m = Milestone(chat_id=90001, milestone_type="first_5k", title="First 5K!")
        result = await db.create_milestone(m)
        assert result.id is not None

    async def test_get_milestones(self, db, sample_runner):
        await db.create_runner(sample_runner)
        await db.create_milestone(
            Milestone(chat_id=90001, milestone_type="first_5k", title="First 5K")
        )
        await db.create_milestone(
            Milestone(chat_id=90001, milestone_type="streak", title="7 Day Streak")
        )
        milestones = await db.get_milestones(90001)
        assert len(milestones) == 2
