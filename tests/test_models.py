from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.models import (
    CoachObservation,
    ConnectedServiceRecord,
    Injury,
    MetricLog,
    Milestone,
    PersonalBest,
    PrimaryGoal,
    Run,
    Runner,
    RunSplit,
    RunningLevel,
    Shoe,
    ShoeType,
    TrainingPhase,
    UserTag,
)


class TestRunnerModel:
    def test_create_minimal_runner(self):
        runner = Runner(chat_id=12345)
        assert runner.chat_id == 12345
        assert runner.running_level == RunningLevel.NEW
        assert runner.primary_goal == PrimaryGoal.FINISH_5K
        assert runner.fatigue_level == 3
        assert runner.name is None

    def test_create_full_runner(self, sample_runner):
        assert sample_runner.name == "Alice"
        assert sample_runner.running_level == RunningLevel.BEGINNER
        assert sample_runner.primary_goal == PrimaryGoal.IMPROVE_5K

    def test_fatigue_level_out_of_range_low(self):
        with pytest.raises(ValidationError):
            Runner(chat_id=1, fatigue_level=0)

    def test_fatigue_level_out_of_range_high(self):
        with pytest.raises(ValidationError):
            Runner(chat_id=1, fatigue_level=6)

    def test_fatigue_level_boundary_valid(self):
        r1 = Runner(chat_id=1, fatigue_level=1)
        assert r1.fatigue_level == 1
        r5 = Runner(chat_id=1, fatigue_level=5)
        assert r5.fatigue_level == 5

    def test_running_level_enum_values(self):
        runner = Runner(chat_id=1, running_level="beginner")
        assert runner.running_level == RunningLevel.BEGINNER

    def test_invalid_running_level(self):
        with pytest.raises(ValidationError):
            Runner(chat_id=1, running_level="super_beginner")

    def test_primary_goal_enum_values(self):
        runner = Runner(chat_id=1, primary_goal="marathon")
        assert runner.primary_goal == PrimaryGoal.MARATHON

    def test_training_phase_default(self):
        runner = Runner(chat_id=1)
        assert runner.training_phase == TrainingPhase.BASE

    def test_date_fields_accept_none(self):
        runner = Runner(chat_id=1, target_race_date=None)
        assert runner.target_race_date is None

    def test_date_fields_accept_date(self):
        d = date(2026, 12, 31)
        runner = Runner(chat_id=1, target_race_date=d)
        assert runner.target_race_date == d


class TestInjuryModel:
    def test_create_minimal_injury(self):
        injury = Injury(chat_id=1, body_part="shin")
        assert injury.body_part == "shin"
        assert injury.active is True

    def test_create_full_injury(self, sample_injury):
        assert sample_injury.body_part == "knee"
        assert sample_injury.injury_type == "runners_knee"
        assert sample_injury.active is True

    def test_severity_enum(self):
        injury = Injury(chat_id=1, body_part="achilles", severity="severe")
        assert injury.severity == "severe"

    def test_invalid_severity(self):
        with pytest.raises(ValidationError):
            Injury(chat_id=1, body_part="knee", severity="critical")


class TestShoeModel:
    def test_create_minimal_shoe(self):
        shoe = Shoe(chat_id=1, name="Test Shoe")
        assert shoe.type == ShoeType.DAILY_TRAINER
        assert shoe.retired is False

    def test_create_full_shoe(self, sample_shoe):
        assert sample_shoe.name == "Nike Pegasus 40"
        assert sample_shoe.type == ShoeType.DAILY_TRAINER

    def test_shoe_type_enum(self):
        shoe = Shoe(chat_id=1, name="Race Shoe", type="race")
        assert shoe.type == ShoeType.RACE


class TestRunModel:
    def test_create_minimal_run(self):
        run = Run(chat_id=1, run_date=date.today())
        assert run.source == "manual"
        assert run.confidence == 1.0

    def test_create_full_run(self, sample_run):
        assert sample_run.distance_km == 5.0
        assert sample_run.run_type == "easy"

    def test_rpe_out_of_range_low(self):
        with pytest.raises(ValidationError):
            Run(chat_id=1, run_date=date.today(), rpe=0)

    def test_rpe_out_of_range_high(self):
        with pytest.raises(ValidationError):
            Run(chat_id=1, run_date=date.today(), rpe=11)

    def test_rpe_boundary_valid(self):
        r1 = Run(chat_id=1, run_date=date.today(), rpe=1)
        assert r1.rpe == 1
        r10 = Run(chat_id=1, run_date=date.today(), rpe=10)
        assert r10.rpe == 10

    def test_rpe_none_valid(self):
        run = Run(chat_id=1, run_date=date.today(), rpe=None)
        assert run.rpe is None

    def test_run_type_enum(self):
        run = Run(chat_id=1, run_date=date.today(), run_type="tempo")
        assert run.run_type == "tempo"


class TestRunSplitModel:
    def test_create_split(self):
        split = RunSplit(run_id=1, split_number=1, distance_m=400, duration_sec=90)
        assert split.split_number == 1
        assert split.recovery_sec is None


class TestPersonalBestModel:
    def test_create_pb(self, sample_pb):
        assert sample_pb.distance == "5k"
        assert sample_pb.time_sec == 1500

    def test_unique_constraint_fields(self):
        pb = PersonalBest(chat_id=1, distance="5k", time_sec=1500)
        assert pb.chat_id == 1
        assert pb.distance == "5k"


class TestMetricLogModel:
    def test_create_metric(self, sample_metric):
        assert sample_metric.category == "body"
        assert sample_metric.metric_name == "weight_kg"
        assert sample_metric.value == 65.0

    def test_category_enum(self):
        metric = MetricLog(
            chat_id=1, category="performance", metric_name="vo2max", value=45
        )
        assert metric.category == "performance"


class TestCoachObservationModel:
    def test_create_observation(self, sample_observation):
        assert sample_observation.category == "motivation"
        assert sample_observation.active is True

    def test_category_enum(self):
        obs = CoachObservation(
            chat_id=1, category="pattern", observation="Skips long runs"
        )
        assert obs.category == "pattern"


class TestConnectedServiceModel:
    def test_create_service(self):
        svc = ConnectedServiceRecord(chat_id=1, service="garmin")
        assert svc.connected is False

    def test_service_enum(self):
        svc = ConnectedServiceRecord(chat_id=1, service="strava")
        assert svc.service == "strava"


class TestMilestoneModel:
    def test_create_milestone(self):
        m = Milestone(chat_id=1, milestone_type="first_5k", title="First 5K!")
        assert m.milestone_type == "first_5k"

    def test_milestone_type_enum(self):
        m = Milestone(chat_id=1, milestone_type="streak", title="7 day streak")
        assert m.milestone_type == "streak"


class TestUserTagModel:
    def test_create_tag(self):
        tag = UserTag(chat_id=1, tag="morning_runner")
        assert tag.tag == "morning_runner"
        assert tag.chat_id == 1
