from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RunningLevel(str, Enum):
    NEW = "new"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PrimaryGoal(str, Enum):
    FINISH_5K = "finish_5k"
    IMPROVE_5K = "improve_5k"
    IMPROVE_10K = "10k"
    HALF_MARATHON = "half_marathon"
    MARATHON = "marathon"
    GENERAL = "general"


class TrainingPhase(str, Enum):
    BASE = "base"
    BUILD = "build"
    PEAK = "peak"
    TAPER = "taper"


class RunType(str, Enum):
    EASY = "easy"
    TEMPO = "tempo"
    INTERVAL = "interval"
    LONG_RUN = "long_run"
    RECOVERY = "recovery"
    RACE = "race"
    OTHER = "other"


class ShoeType(str, Enum):
    DAILY_TRAINER = "daily_trainer"
    SPEED = "speed"
    RACE = "race"
    TRAIL = "trail"


class InjurySeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class WeatherCondition(str, Enum):
    CLEAR = "clear"
    RAIN = "rain"
    HOT = "hot"
    WINDY = "windy"
    STORM = "storm"
    COLD = "cold"


class MetricCategory(str, Enum):
    BODY = "body"
    RECOVERY = "recovery"
    PERFORMANCE = "performance"


class ObservationCategory(str, Enum):
    PERSONALITY = "personality"
    MOTIVATION = "motivation"
    PATTERN = "pattern"
    PREFERENCE = "preference"
    PLAN = "plan"


class MilestoneType(str, Enum):
    FIRST_5K = "first_5k"
    FIRST_10K = "first_10k"
    DISTANCE_PR = "distance_pr"
    STREAK = "streak"
    TOTAL_KM = "total_km"


class DataSource(str, Enum):
    MANUAL = "manual"
    GARMIN = "garmin"
    STRAVA = "strava"
    SCREENSHOT = "screenshot"


class ConnectedService(str, Enum):
    GARMIN = "garmin"
    STRAVA = "strava"


class Runner(BaseModel):
    chat_id: int
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    running_level: RunningLevel = RunningLevel.NEW
    primary_goal: PrimaryGoal = PrimaryGoal.FINISH_5K
    target_race_name: Optional[str] = None
    target_race_date: Optional[date] = None
    target_race_time_sec: Optional[int] = None
    running_history_months: int = 0
    current_weekly_km: float = 0
    preferred_days: Optional[str] = None
    preferred_time: str = "morning"
    max_session_minutes: int = 60
    current_program: Optional[str] = None
    program_started: Optional[date] = None
    week_of_program: int = 1
    training_phase: TrainingPhase = TrainingPhase.BASE
    fatigue_level: int = Field(default=3, ge=1, le=5)
    consistency_30d: float = 0
    streak_days: int = 0
    resting_hr: Optional[int] = None
    hr_variability: Optional[int] = None
    vo2max_estimate: Optional[float] = None
    cadence_avg: Optional[int] = None
    language: str = "en"
    communication_style: str = "casual"
    detail_level: str = "detailed"
    location_city: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    location_timezone: Optional[str] = None
    weather_enabled: bool = False
    last_active: Optional[date] = None
    total_runs: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("fatigue_level")
    @classmethod
    def validate_fatigue(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("fatigue_level must be between 1 and 5")
        return v


class Injury(BaseModel):
    id: Optional[int] = None
    chat_id: int
    body_part: str
    injury_type: Optional[str] = None
    description: Optional[str] = None
    severity: InjurySeverity = InjurySeverity.MILD
    onset_date: Optional[date] = None
    resolved_date: Optional[date] = None
    active: bool = True
    modified_training: Optional[str] = None
    source: str = "conversation"
    created_at: Optional[datetime] = None


class Shoe(BaseModel):
    id: Optional[int] = None
    chat_id: int
    name: str
    type: ShoeType = ShoeType.DAILY_TRAINER
    km_on_shoes: float = 0
    added_date: Optional[date] = None
    retired: bool = False


class Run(BaseModel):
    id: Optional[int] = None
    chat_id: int
    run_date: date
    run_type: Optional[RunType] = None
    distance_km: Optional[float] = None
    duration_sec: Optional[int] = None
    avg_pace_sec_per_km: Optional[float] = None
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None
    cadence_avg: Optional[int] = None
    elevation_gain_m: int = 0
    rpe: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = None
    shoe_id: Optional[int] = None
    weather_temp_c: Optional[float] = None
    weather_condition: Optional[WeatherCondition] = None
    weather_impact: Optional[str] = None
    source: DataSource = DataSource.MANUAL
    confidence: float = 1.0
    created_at: Optional[datetime] = None

    @field_validator("rpe")
    @classmethod
    def validate_rpe(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 10):
            raise ValueError("rpe must be between 1 and 10")
        return v


class RunSplit(BaseModel):
    id: Optional[int] = None
    run_id: int
    split_number: int
    distance_m: float
    duration_sec: float
    recovery_sec: Optional[float] = None


class PersonalBest(BaseModel):
    id: Optional[int] = None
    chat_id: int
    distance: str
    time_sec: int
    achieved_date: Optional[date] = None
    run_id: Optional[int] = None


class MetricLog(BaseModel):
    id: Optional[int] = None
    chat_id: int
    category: MetricCategory
    metric_name: str
    value: float
    unit: Optional[str] = None
    source: str = "manual"
    confidence: float = 1.0
    recorded_at: Optional[datetime] = None


class CoachObservation(BaseModel):
    id: Optional[int] = None
    chat_id: int
    category: ObservationCategory
    observation: str
    evidence: Optional[str] = None
    confidence: int = 1
    first_observed: Optional[date] = None
    last_observed: Optional[date] = None
    active: bool = True


class ConnectedServiceRecord(BaseModel):
    id: Optional[int] = None
    chat_id: int
    service: ConnectedService
    connected: bool = False
    scopes: Optional[str] = None
    token_encrypted: Optional[str] = None
    last_sync: Optional[datetime] = None
    last_sync_status: Optional[str] = None


class Milestone(BaseModel):
    id: Optional[int] = None
    chat_id: int
    milestone_type: MilestoneType
    title: str
    value: Optional[str] = None
    achieved_date: Optional[date] = None
    created_at: Optional[datetime] = None


class UserTag(BaseModel):
    chat_id: int
    tag: str
