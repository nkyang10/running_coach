from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional

import aiosqlite

from app.logger import get_logger
from app.models import (
    CoachObservation,
    ConnectedServiceRecord,
    Injury,
    MetricLog,
    Milestone,
    PersonalBest,
    Run,
    Runner,
    RunSplit,
    Shoe,
    UserTag,
)

logger = get_logger(__name__)

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS runners (
    chat_id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER,
    gender TEXT,
    running_level TEXT DEFAULT 'new',
    primary_goal TEXT DEFAULT 'finish_5k',
    target_race_name TEXT,
    target_race_date DATE,
    target_race_time_sec INTEGER,
    running_history_months INTEGER DEFAULT 0,
    current_weekly_km REAL DEFAULT 0,
    preferred_days TEXT,
    preferred_time TEXT DEFAULT 'morning',
    max_session_minutes INTEGER DEFAULT 60,
    current_program TEXT,
    program_started DATE,
    week_of_program INTEGER DEFAULT 1,
    training_phase TEXT DEFAULT 'base',
    fatigue_level INTEGER DEFAULT 3,
    consistency_30d REAL DEFAULT 0,
    streak_days INTEGER DEFAULT 0,
    resting_hr INTEGER,
    hr_variability INTEGER,
    vo2max_estimate REAL,
    cadence_avg INTEGER,
    language TEXT DEFAULT 'en',
    communication_style TEXT DEFAULT 'casual',
    detail_level TEXT DEFAULT 'detailed',
    location_city TEXT,
    location_lat REAL,
    location_lon REAL,
    location_timezone TEXT,
    weather_enabled BOOLEAN DEFAULT 0,
    last_active DATE,
    total_runs INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS injuries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    body_part TEXT NOT NULL,
    injury_type TEXT,
    description TEXT,
    severity TEXT DEFAULT 'mild',
    onset_date DATE,
    resolved_date DATE,
    active BOOLEAN DEFAULT 1,
    modified_training TEXT,
    source TEXT DEFAULT 'conversation',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    name TEXT NOT NULL,
    type TEXT DEFAULT 'daily_trainer',
    km_on_shoes REAL DEFAULT 0,
    added_date DATE DEFAULT (date('now')),
    retired BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    run_date DATE DEFAULT (date('now')),
    run_type TEXT,
    distance_km REAL,
    duration_sec INTEGER,
    avg_pace_sec_per_km REAL,
    avg_hr INTEGER,
    max_hr INTEGER,
    cadence_avg INTEGER,
    elevation_gain_m INTEGER DEFAULT 0,
    rpe INTEGER,
    notes TEXT,
    shoe_id INTEGER REFERENCES shoes(id),
    weather_temp_c REAL,
    weather_condition TEXT,
    weather_impact TEXT,
    source TEXT DEFAULT 'manual',
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS run_splits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id),
    split_number INTEGER,
    distance_m REAL,
    duration_sec REAL,
    recovery_sec REAL
);

CREATE TABLE IF NOT EXISTS personal_bests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    distance TEXT NOT NULL,
    time_sec INTEGER NOT NULL,
    achieved_date DATE,
    run_id INTEGER REFERENCES runs(id),
    UNIQUE(chat_id, distance)
);

CREATE TABLE IF NOT EXISTS metric_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    category TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT,
    source TEXT DEFAULT 'manual',
    confidence REAL DEFAULT 1.0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS coach_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    category TEXT NOT NULL,
    observation TEXT NOT NULL,
    evidence TEXT,
    confidence INTEGER DEFAULT 1,
    first_observed DATE,
    last_observed DATE,
    active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS connected_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    service TEXT NOT NULL,
    connected BOOLEAN DEFAULT 0,
    scopes TEXT,
    token_encrypted TEXT,
    last_sync TIMESTAMP,
    last_sync_status TEXT,
    UNIQUE(chat_id, service)
);

CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    milestone_type TEXT NOT NULL,
    title TEXT NOT NULL,
    value TEXT,
    achieved_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_tags (
    chat_id INTEGER REFERENCES runners(chat_id),
    tag TEXT NOT NULL,
    UNIQUE(chat_id, tag)
);
"""

CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_runs_chat ON runs(chat_id);",
    "CREATE INDEX IF NOT EXISTS idx_runs_date ON runs(run_date);",
    "CREATE INDEX IF NOT EXISTS idx_runs_type ON runs(run_type);",
    "CREATE INDEX IF NOT EXISTS idx_metric_log_chat ON metric_log(chat_id);",
    "CREATE INDEX IF NOT EXISTS idx_metric_log_name ON metric_log(metric_name);",
    "CREATE INDEX IF NOT EXISTS idx_injuries_chat ON injuries(chat_id);",
    "CREATE INDEX IF NOT EXISTS idx_shoes_chat ON shoes(chat_id);",
    "CREATE INDEX IF NOT EXISTS idx_observations_chat ON coach_observations(chat_id);",
    "CREATE INDEX IF NOT EXISTS idx_splits_run ON run_splits(run_id);",
]


class Database:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._conn: Optional[aiosqlite.Connection] = None
        aiosqlite.register_adapter(date, lambda d: d.isoformat())
        aiosqlite.register_adapter(datetime, lambda d: d.isoformat())

    async def connect(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(str(self.db_path))
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")
        logger.info("database_connected", path=str(self.db_path))

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("database_disconnected")

    async def init_tables(self) -> None:
        assert self._conn
        await self._conn.executescript(CREATE_TABLES_SQL)
        for sql in CREATE_INDEXES_SQL:
            await self._conn.execute(sql)
        await self._conn.commit()
        logger.info("database_tables_initialized")

    @property
    def conn(self) -> aiosqlite.Connection:
        assert self._conn
        return self._conn

    async def execute(self, sql: str, params: tuple = ()) -> aiosqlite.Cursor:
        return await self.conn.execute(sql, params)

    async def executemany(self, sql: str, params: list[tuple]) -> None:
        await self.conn.executemany(sql, params)
        await self.conn.commit()

    async def fetchone(self, sql: str, params: tuple = ()) -> Optional[aiosqlite.Row]:
        cursor = await self.conn.execute(sql, params)
        return await cursor.fetchone()

    async def fetchall(self, sql: str, params: tuple = ()) -> list[aiosqlite.Row]:
        cursor = await self.conn.execute(sql, params)
        return await cursor.fetchall()

    async def commit(self) -> None:
        await self.conn.commit()

    # ─── Runner CRUD ───

    async def create_runner(self, runner: Runner) -> Runner:
        now = datetime.now(timezone.utc)
        await self.execute(
            """INSERT INTO runners (chat_id, name, age, gender, running_level, primary_goal,
               target_race_name, target_race_date, target_race_time_sec, running_history_months,
               current_weekly_km, preferred_days, preferred_time, max_session_minutes,
               current_program, program_started, week_of_program, training_phase, fatigue_level,
               consistency_30d, streak_days, resting_hr, hr_variability, vo2max_estimate,
               cadence_avg, language, communication_style, detail_level, location_city,
               location_lat, location_lon, location_timezone, weather_enabled, last_active,
               total_runs, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                runner.chat_id, runner.name, runner.age, runner.gender,
                runner.running_level.value, runner.primary_goal.value,
                runner.target_race_name, runner.target_race_date,
                runner.target_race_time_sec, runner.running_history_months,
                runner.current_weekly_km, runner.preferred_days, runner.preferred_time,
                runner.max_session_minutes, runner.current_program, runner.program_started,
                runner.week_of_program, runner.training_phase.value, runner.fatigue_level,
                runner.consistency_30d, runner.streak_days, runner.resting_hr,
                runner.hr_variability, runner.vo2max_estimate, runner.cadence_avg,
                runner.language, runner.communication_style, runner.detail_level,
                runner.location_city, runner.location_lat, runner.location_lon,
                runner.location_timezone, int(runner.weather_enabled), runner.last_active,
                runner.total_runs, now, now,
            ),
        )
        await self.commit()
        runner.created_at = now
        runner.updated_at = now
        logger.info("runner_created", chat_id=runner.chat_id)
        return runner

    async def get_runner(self, chat_id: int) -> Optional[Runner]:
        row = await self.fetchone("SELECT * FROM runners WHERE chat_id = ?", (chat_id,))
        if row is None:
            return None
        return self._row_to_runner(row)

    async def update_runner(self, runner: Runner) -> Runner:
        runner.updated_at = datetime.now(timezone.utc)
        await self.execute(
            """UPDATE runners SET name=?, age=?, gender=?, running_level=?, primary_goal=?,
               target_race_name=?, target_race_date=?, target_race_time_sec=?,
               running_history_months=?, current_weekly_km=?, preferred_days=?,
               preferred_time=?, max_session_minutes=?, current_program=?, program_started=?,
               week_of_program=?, training_phase=?, fatigue_level=?, consistency_30d=?,
               streak_days=?, resting_hr=?, hr_variability=?, vo2max_estimate=?, cadence_avg=?,
               language=?, communication_style=?, detail_level=?, location_city=?,
               location_lat=?, location_lon=?, location_timezone=?, weather_enabled=?,
               last_active=?, total_runs=?, updated_at=?
               WHERE chat_id=?""",
            (
                runner.name, runner.age, runner.gender, runner.running_level.value,
                runner.primary_goal.value, runner.target_race_name, runner.target_race_date,
                runner.target_race_time_sec, runner.running_history_months,
                runner.current_weekly_km, runner.preferred_days, runner.preferred_time,
                runner.max_session_minutes, runner.current_program, runner.program_started,
                runner.week_of_program, runner.training_phase.value, runner.fatigue_level,
                runner.consistency_30d, runner.streak_days, runner.resting_hr,
                runner.hr_variability, runner.vo2max_estimate, runner.cadence_avg,
                runner.language, runner.communication_style, runner.detail_level,
                runner.location_city, runner.location_lat, runner.location_lon,
                runner.location_timezone, int(runner.weather_enabled), runner.last_active,
                runner.total_runs, runner.updated_at, runner.chat_id,
            ),
        )
        await self.commit()
        return runner

    async def delete_runner(self, chat_id: int) -> bool:
        cursor = await self.execute("DELETE FROM runners WHERE chat_id = ?", (chat_id,))
        await self.commit()
        return cursor.rowcount > 0

    async def get_all_runners(self) -> list[Runner]:
        rows = await self.fetchall("SELECT * FROM runners ORDER BY last_active DESC")
        return [self._row_to_runner(r) for r in rows]

    async def get_runner_count(self) -> int:
        row = await self.fetchone("SELECT COUNT(*) as cnt FROM runners")
        return row["cnt"] if row else 0

    def _row_to_runner(self, row: aiosqlite.Row) -> Runner:
        return Runner(
            chat_id=row["chat_id"],
            name=row["name"],
            age=row["age"],
            gender=row["gender"],
            running_level=row["running_level"],
            primary_goal=row["primary_goal"],
            target_race_name=row["target_race_name"],
            target_race_date=self._parse_date(row["target_race_date"]),
            target_race_time_sec=row["target_race_time_sec"],
            running_history_months=row["running_history_months"],
            current_weekly_km=row["current_weekly_km"],
            preferred_days=row["preferred_days"],
            preferred_time=row["preferred_time"],
            max_session_minutes=row["max_session_minutes"],
            current_program=row["current_program"],
            program_started=self._parse_date(row["program_started"]),
            week_of_program=row["week_of_program"],
            training_phase=self._safe_enum(row["training_phase"]),
            fatigue_level=row["fatigue_level"],
            consistency_30d=row["consistency_30d"],
            streak_days=row["streak_days"],
            resting_hr=row["resting_hr"],
            hr_variability=row["hr_variability"],
            vo2max_estimate=row["vo2max_estimate"],
            cadence_avg=row["cadence_avg"],
            language=row["language"],
            communication_style=row["communication_style"],
            detail_level=row["detail_level"],
            location_city=row["location_city"],
            location_lat=row["location_lat"],
            location_lon=row["location_lon"],
            location_timezone=row["location_timezone"],
            weather_enabled=bool(row["weather_enabled"]),
            last_active=self._parse_date(row["last_active"]),
            total_runs=row["total_runs"],
            created_at=self._parse_datetime(row["created_at"]),
            updated_at=self._parse_datetime(row["updated_at"]),
        )

    # ─── Injury CRUD ───

    async def create_injury(self, injury: Injury) -> Injury:
        cursor = await self.execute(
            """INSERT INTO injuries (chat_id, body_part, injury_type, description, severity,
               onset_date, resolved_date, active, modified_training, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                injury.chat_id, injury.body_part, injury.injury_type, injury.description,
                injury.severity.value if injury.severity else "mild",
                injury.onset_date, injury.resolved_date, int(injury.active),
                injury.modified_training, injury.source,
            ),
        )
        await self.commit()
        injury.id = cursor.lastrowid
        return injury

    async def get_injuries(self, chat_id: int, active_only: bool = True) -> list[Injury]:
        if active_only:
            rows = await self.fetchall(
                "SELECT * FROM injuries WHERE chat_id = ? AND active = 1 ORDER BY onset_date DESC",
                (chat_id,),
            )
        else:
            rows = await self.fetchall(
                "SELECT * FROM injuries WHERE chat_id = ? ORDER BY onset_date DESC",
                (chat_id,),
            )
        return [self._row_to_injury(r) for r in rows]

    async def update_injury(self, injury: Injury) -> Injury:
        await self.execute(
            """UPDATE injuries SET body_part=?, injury_type=?, description=?, severity=?,
               onset_date=?, resolved_date=?, active=?, modified_training=?, source=?
               WHERE id=?""",
            (
                injury.body_part, injury.injury_type, injury.description,
                injury.severity.value if injury.severity else "mild",
                injury.onset_date, injury.resolved_date, int(injury.active),
                injury.modified_training, injury.source, injury.id,
            ),
        )
        await self.commit()
        return injury

    def _row_to_injury(self, row: aiosqlite.Row) -> Injury:
        return Injury(
            id=row["id"],
            chat_id=row["chat_id"],
            body_part=row["body_part"],
            injury_type=row["injury_type"],
            description=row["description"],
            severity=row["severity"],
            onset_date=self._parse_date(row["onset_date"]),
            resolved_date=self._parse_date(row["resolved_date"]),
            active=bool(row["active"]),
            modified_training=row["modified_training"],
            source=row["source"],
            created_at=self._parse_datetime(row["created_at"]),
        )

    # ─── Shoe CRUD ───

    async def create_shoe(self, shoe: Shoe) -> Shoe:
        cursor = await self.execute(
            """INSERT INTO shoes (chat_id, name, type, km_on_shoes, added_date, retired)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                shoe.chat_id, shoe.name, shoe.type.value if shoe.type else "daily_trainer",
                shoe.km_on_shoes, shoe.added_date, int(shoe.retired),
            ),
        )
        await self.commit()
        shoe.id = cursor.lastrowid
        return shoe

    async def get_shoes(self, chat_id: int, active_only: bool = True) -> list[Shoe]:
        if active_only:
            rows = await self.fetchall(
                "SELECT * FROM shoes WHERE chat_id = ? AND retired = 0 ORDER BY added_date DESC",
                (chat_id,),
            )
        else:
            rows = await self.fetchall(
                "SELECT * FROM shoes WHERE chat_id = ? ORDER BY added_date DESC", (chat_id,),
            )
        return [self._row_to_shoe(r) for r in rows]

    async def update_shoe(self, shoe: Shoe) -> Shoe:
        await self.execute(
            """UPDATE shoes SET name=?, type=?, km_on_shoes=?, added_date=?, retired=?
               WHERE id=?""",
            (shoe.name, shoe.type.value if shoe.type else "daily_trainer",
             shoe.km_on_shoes, shoe.added_date, int(shoe.retired), shoe.id),
        )
        await self.commit()
        return shoe

    def _row_to_shoe(self, row: aiosqlite.Row) -> Shoe:
        return Shoe(
            id=row["id"],
            chat_id=row["chat_id"],
            name=row["name"],
            type=row["type"],
            km_on_shoes=row["km_on_shoes"],
            added_date=self._parse_date(row["added_date"]),
            retired=bool(row["retired"]),
        )

    # ─── Run CRUD ───

    async def create_run(self, run: Run) -> Run:
        cursor = await self.execute(
            """INSERT INTO runs (chat_id, run_date, run_type, distance_km, duration_sec,
               avg_pace_sec_per_km, avg_hr, max_hr, cadence_avg, elevation_gain_m, rpe, notes,
               shoe_id, weather_temp_c, weather_condition, weather_impact, source, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run.chat_id, run.run_date, run.run_type.value if run.run_type else None,
                run.distance_km, run.duration_sec, run.avg_pace_sec_per_km, run.avg_hr,
                run.max_hr, run.cadence_avg, run.elevation_gain_m, run.rpe, run.notes,
                run.shoe_id, run.weather_temp_c,
                run.weather_condition.value if run.weather_condition else None,
                run.weather_impact, run.source.value, run.confidence,
            ),
        )
        await self.commit()
        run.id = cursor.lastrowid
        return run

    async def get_runs(
        self, chat_id: int, limit: int = 20, offset: int = 0
    ) -> list[Run]:
        rows = await self.fetchall(
            "SELECT * FROM runs WHERE chat_id = ? ORDER BY run_date DESC LIMIT ? OFFSET ?",
            (chat_id, limit, offset),
        )
        return [self._row_to_run(r) for r in rows]

    async def get_run(self, run_id: int) -> Optional[Run]:
        row = await self.fetchone("SELECT * FROM runs WHERE id = ?", (run_id,))
        if row is None:
            return None
        return self._row_to_run(row)

    async def get_recent_runs(self, chat_id: int, days: int = 30) -> list[Run]:
        rows = await self.fetchall(
            "SELECT * FROM runs WHERE chat_id = ? AND run_date >= date('now', ?) ORDER BY run_date DESC",
            (chat_id, f"-{days} days"),
        )
        return [self._row_to_run(r) for r in rows]

    def _row_to_run(self, row: aiosqlite.Row) -> Run:
        return Run(
            id=row["id"],
            chat_id=row["chat_id"],
            run_date=self._parse_date(row["run_date"]),
            run_type=row["run_type"],
            distance_km=row["distance_km"],
            duration_sec=row["duration_sec"],
            avg_pace_sec_per_km=row["avg_pace_sec_per_km"],
            avg_hr=row["avg_hr"],
            max_hr=row["max_hr"],
            cadence_avg=row["cadence_avg"],
            elevation_gain_m=row["elevation_gain_m"],
            rpe=row["rpe"],
            notes=row["notes"],
            shoe_id=row["shoe_id"],
            weather_temp_c=row["weather_temp_c"],
            weather_condition=row["weather_condition"],
            weather_impact=row["weather_impact"],
            source=row["source"],
            confidence=row["confidence"],
            created_at=self._parse_datetime(row["created_at"]),
        )

    # ─── Run Splits CRUD ───

    async def create_run_split(self, split: RunSplit) -> RunSplit:
        cursor = await self.execute(
            """INSERT INTO run_splits (run_id, split_number, distance_m, duration_sec, recovery_sec)
               VALUES (?, ?, ?, ?, ?)""",
            (split.run_id, split.split_number, split.distance_m, split.duration_sec, split.recovery_sec),
        )
        await self.commit()
        split.id = cursor.lastrowid
        return split

    async def get_run_splits(self, run_id: int) -> list[RunSplit]:
        rows = await self.fetchall(
            "SELECT * FROM run_splits WHERE run_id = ? ORDER BY split_number", (run_id,),
        )
        return [self._row_to_split(r) for r in rows]

    def _row_to_split(self, row: aiosqlite.Row) -> RunSplit:
        return RunSplit(
            id=row["id"], run_id=row["run_id"], split_number=row["split_number"],
            distance_m=row["distance_m"], duration_sec=row["duration_sec"],
            recovery_sec=row["recovery_sec"],
        )

    # ─── Personal Best CRUD ───

    async def upsert_personal_best(self, pb: PersonalBest) -> PersonalBest:
        existing = await self.fetchone(
            "SELECT id FROM personal_bests WHERE chat_id = ? AND distance = ?",
            (pb.chat_id, pb.distance),
        )
        if existing:
            await self.execute(
                "UPDATE personal_bests SET time_sec=?, achieved_date=?, run_id=? WHERE id=?",
                (pb.time_sec, pb.achieved_date, pb.run_id, existing["id"]),
            )
            pb.id = existing["id"]
        else:
            cursor = await self.execute(
                "INSERT INTO personal_bests (chat_id, distance, time_sec, achieved_date, run_id) VALUES (?, ?, ?, ?, ?)",
                (pb.chat_id, pb.distance, pb.time_sec, pb.achieved_date, pb.run_id),
            )
            pb.id = cursor.lastrowid
        await self.commit()
        return pb

    async def get_personal_bests(self, chat_id: int) -> list[PersonalBest]:
        rows = await self.fetchall(
            "SELECT * FROM personal_bests WHERE chat_id = ? ORDER BY distance", (chat_id,),
        )
        return [self._row_to_pb(r) for r in rows]

    def _row_to_pb(self, row: aiosqlite.Row) -> PersonalBest:
        return PersonalBest(
            id=row["id"], chat_id=row["chat_id"], distance=row["distance"],
            time_sec=row["time_sec"], achieved_date=self._parse_date(row["achieved_date"]),
            run_id=row["run_id"],
        )

    # ─── Metric Log CRUD ───

    async def create_metric(self, metric: MetricLog) -> MetricLog:
        cursor = await self.execute(
            "INSERT INTO metric_log (chat_id, category, metric_name, value, unit, source, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                metric.chat_id, metric.category.value if metric.category else "body",
                metric.metric_name, metric.value, metric.unit, metric.source, metric.confidence,
            ),
        )
        await self.commit()
        metric.id = cursor.lastrowid
        return metric

    async def get_metrics(
        self, chat_id: int, metric_name: str, limit: int = 30
    ) -> list[MetricLog]:
        rows = await self.fetchall(
            "SELECT * FROM metric_log WHERE chat_id = ? AND metric_name = ? ORDER BY recorded_at DESC LIMIT ?",
            (chat_id, metric_name, limit),
        )
        return [self._row_to_metric(r) for r in rows]

    def _row_to_metric(self, row: aiosqlite.Row) -> MetricLog:
        return MetricLog(
            id=row["id"], chat_id=row["chat_id"], category=row["category"],
            metric_name=row["metric_name"], value=row["value"], unit=row["unit"],
            source=row["source"], confidence=row["confidence"],
            recorded_at=self._parse_datetime(row["recorded_at"]),
        )

    # ─── Coach Observation CRUD ───

    async def create_observation(self, obs: CoachObservation) -> CoachObservation:
        obs.first_observed = obs.first_observed or date.today()
        obs.last_observed = date.today()
        cursor = await self.execute(
            "INSERT INTO coach_observations (chat_id, category, observation, evidence, confidence, first_observed, last_observed, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                obs.chat_id, obs.category.value if obs.category else "pattern",
                obs.observation, obs.evidence, obs.confidence,
                obs.first_observed, obs.last_observed, int(obs.active),
            ),
        )
        await self.commit()
        obs.id = cursor.lastrowid
        return obs

    async def get_observations(self, chat_id: int, active_only: bool = True) -> list[CoachObservation]:
        if active_only:
            rows = await self.fetchall(
                "SELECT * FROM coach_observations WHERE chat_id = ? AND active = 1 ORDER BY last_observed DESC",
                (chat_id,),
            )
        else:
            rows = await self.fetchall(
                "SELECT * FROM coach_observations WHERE chat_id = ? ORDER BY last_observed DESC",
                (chat_id,),
            )
        return [self._row_to_obs(r) for r in rows]

    def _row_to_obs(self, row: aiosqlite.Row) -> CoachObservation:
        return CoachObservation(
            id=row["id"], chat_id=row["chat_id"], category=row["category"],
            observation=row["observation"], evidence=row["evidence"],
            confidence=row["confidence"],
            first_observed=self._parse_date(row["first_observed"]),
            last_observed=self._parse_date(row["last_observed"]),
            active=bool(row["active"]),
        )

    # ─── Connected Services CRUD ───

    async def upsert_connected_service(self, svc: ConnectedServiceRecord) -> ConnectedServiceRecord:
        await self.execute(
            "INSERT OR REPLACE INTO connected_services (chat_id, service, connected, scopes, token_encrypted, last_sync, last_sync_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                svc.chat_id, svc.service.value if svc.service else "garmin",
                int(svc.connected), svc.scopes, svc.token_encrypted,
                svc.last_sync, svc.last_sync_status,
            ),
        )
        await self.commit()
        return svc

    async def get_connected_services(self, chat_id: int) -> list[ConnectedServiceRecord]:
        rows = await self.fetchall(
            "SELECT * FROM connected_services WHERE chat_id = ?", (chat_id,),
        )
        return [self._row_to_svc(r) for r in rows]

    def _row_to_svc(self, row: aiosqlite.Row) -> ConnectedServiceRecord:
        return ConnectedServiceRecord(
            id=row["id"], chat_id=row["chat_id"], service=row["service"],
            connected=bool(row["connected"]), scopes=row["scopes"],
            token_encrypted=row["token_encrypted"],
            last_sync=self._parse_datetime(row["last_sync"]),
            last_sync_status=row["last_sync_status"],
        )

    # ─── Milestone CRUD ───

    async def create_milestone(self, milestone: Milestone) -> Milestone:
        cursor = await self.execute(
            "INSERT INTO milestones (chat_id, milestone_type, title, value, achieved_date) VALUES (?, ?, ?, ?, ?)",
            (
                milestone.chat_id, milestone.milestone_type.value if milestone.milestone_type else "streak",
                milestone.title, milestone.value, milestone.achieved_date,
            ),
        )
        await self.commit()
        milestone.id = cursor.lastrowid
        return milestone

    async def get_milestones(self, chat_id: int) -> list[Milestone]:
        rows = await self.fetchall(
            "SELECT * FROM milestones WHERE chat_id = ? ORDER BY achieved_date DESC", (chat_id,),
        )
        return [self._row_to_milestone(r) for r in rows]

    def _row_to_milestone(self, row: aiosqlite.Row) -> Milestone:
        return Milestone(
            id=row["id"], chat_id=row["chat_id"], milestone_type=row["milestone_type"],
            title=row["title"], value=row["value"],
            achieved_date=self._parse_date(row["achieved_date"]),
            created_at=self._parse_datetime(row["created_at"]),
        )

    # ─── Tags CRUD ───

    async def add_tag(self, chat_id: int, tag: str) -> None:
        await self.execute(
            "INSERT OR IGNORE INTO user_tags (chat_id, tag) VALUES (?, ?)", (chat_id, tag),
        )
        await self.commit()

    async def remove_tag(self, chat_id: int, tag: str) -> None:
        await self.execute(
            "DELETE FROM user_tags WHERE chat_id = ? AND tag = ?", (chat_id, tag),
        )
        await self.commit()

    async def get_tags(self, chat_id: int) -> list[str]:
        rows = await self.fetchall(
            "SELECT tag FROM user_tags WHERE chat_id = ? ORDER BY tag", (chat_id,),
        )
        return [r["tag"] for r in rows]

    # ─── Helpers ───

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_enum(value: Optional[str]) -> Optional[str]:
        return value if value else None
