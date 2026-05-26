# AI Running Coach — Data Structure & Storage

> User Profile, Database Schema, Data Flow
> Target: Running, with cross-training support

---

## Design Principle

```
Runner Data = F(Structured Source, Unstructured Source, Conversation Inference)
              ↑ Garmin/Strava      ↑ Screenshot OCR       ↑ Coach discussion
              ↑ API (exact)        ↑ Vision (approx)       ↑ AI extraction
```

Garmin/Strava is primary for running. Screenshots fill the gap before linking accounts.
Conversation captures subjective feel — "legs felt heavy today" matters as much as pace.

---

## User Profile Structure

```
Runner Profile (per user)
│
├── 📋 Identity & Goals
│   ├── name, age, gender
│   ├── running_level: "new" / "beginner" / "intermediate" / "advanced"
│   ├── primary_goal: "finish_5k" / "improve_5k" / "10k" / "half_marathon" / "marathon" / "general"
│   ├── target_race: {distance, date, goal_time}
│   ├── running_history_months: int
│   └── current_weekly_km: float
│
├── ⚕️ Health & Injuries
│   ├── active_injuries: list[Injury]
│   │   ├── body_part: "shin" / "knee" / "achilles" / "hip" / "foot" / "it_band"
│   │   ├── type: "shin_splints" / "runners_knee" / "plantar_fasciitis" / "itbs" / "achilles_tendinopathy"
│   │   ├── severity: "mild" / "moderate" / "severe"
│   │   ├── onset_date: date
│   │   └── modified_training: "no speed work" / "reduced mileage" / "pool running only"
│   ├── past_injuries: list[Injury]
│   └── medical_conditions: ["exercise-induced asthma", ...]
│
├── 👟 Gear
│   ├── shoes: list[Shoe]
│   │   ├── name: "Nike Pegasus 40"
│   │   ├── type: "daily_trainer" / "speed" / "race" / "trail"
│   │   ├── km_on_shoes: float
│   │   └── added_date: date
│   ├── watch: "garmin_forerunner_255" / "apple_watch" / "coros" / "none"
│   └── hr_monitor: "wrist" / "chest_strap" / "none"
│
├── 📅 Schedule
│   ├── preferred_days: [0, 2, 4, 5]  (Mon/Wed/Fri/Sat → 4 days)
│   ├── preferred_time: "morning" / "lunch" / "evening"
│   ├── max_session_minutes: int
│   └── notes: "long run must be Saturday morning"
│
├── 📊 Current Training Status
│   ├── current_program: "couch_to_5k" / "5k_improver" / "half_marathon" / "custom"
│   ├── week_of_program: int
│   ├── current_weekly_km: float
│   ├── training_phase: "base" / "build" / "peak" / "taper"
│   ├── fatigue_level: 1-5
│   ├── consistency_30d: float (0.0-1.0)
│   └── streak_days: int
│
├── 📈 Performance Metrics
│   ├── recent_runs: list[RunSummary]
│   │   ├── date, type, distance_km, duration_min, avg_pace, avg_hr, rpe
│   │   └── notes
│   ├── personal_bests:
│   │   ├── 1km: {time, date}
│   │   ├── 5k: {time, date}
│   │   ├── 10k: {time, date}
│   │   ├── half_marathon: {time, date} | None
│   │   └── marathon: {time, date} | None
│   ├── vo2max_estimate: float | None  (from Garmin or race predictor)
│   ├── resting_hr: int | None          (from Garmin, daily sync)
│   ├── hr_variability: int | None
│   ├── cadence_avg: int | None         (steps per minute)
│   └── body_metrics:
│       ├── weight: [(date, kg), ...]
│       └── sleep_hours: [(date, hours), ...]
│
├── 🧠 Coach Observations (conversation-inferred)
│   ├── personality_traits: ["data-driven", "needs external motivation", "over-trains easily"]
│   ├── communication_preferences: {language, detail_level, encouragement_style}
│   ├── motivation_triggers: ["likes seeing pace improvement", "responds to streak tracking"]
│   └── common_patterns: ["fatigue on Thursday after hard Wednesday", "skips when raining"]
│
├── 🔌 Connected Services
│   ├── garmin: {connected, last_sync, scopes, token}
│   ├── strava: {connected, last_sync, scopes, token}
│   └── preferred_source: "garmin" / "strava" / "manual"
│
├── 📍 Location & Weather
│   ├── location_city: str | None         ← "Hong Kong" / "Taipei" / "Tokyo"
│   ├── location_lat: float | None        ← auto-resolved from city
│   ├── location_lon: float | None        ← auto-resolved from city
│   ├── location_timezone: str | None     ← "Asia/Hong_Kong"
│   └── weather_enabled: bool             ← consent to use weather data
│
└── 🏷️ Tags & Milestones
    ├── tags: ["trail_runner", "morning_runner", "treadmill_winter"]
    └── milestones: [{"first 5K": date}, {"first 10K": date}, {"100th run": date}, {"sub-25 5K": date}]
```

---

## Database Schema (SQLite)

```sql
-- ==========================================
-- RUNNERS
-- ==========================================

CREATE TABLE runners (
    chat_id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER,
    gender TEXT,
    running_level TEXT DEFAULT 'new',         -- new / beginner / intermediate / advanced
    primary_goal TEXT DEFAULT 'finish_5k',
    target_race_name TEXT,
    target_race_date DATE,
    target_race_time_sec INTEGER,             -- goal time in seconds (nullable)
    running_history_months INTEGER DEFAULT 0,
    current_weekly_km REAL DEFAULT 0,
    preferred_days TEXT,                      -- JSON: [0,2,4,5]
    preferred_time TEXT DEFAULT 'morning',
    max_session_minutes INTEGER DEFAULT 60,
    current_program TEXT,
    program_started DATE,
    week_of_program INTEGER DEFAULT 1,
    training_phase TEXT DEFAULT 'base',       -- base / build / peak / taper
    fatigue_level INTEGER DEFAULT 3,          -- 1-5
    consistency_30d REAL DEFAULT 0,
    streak_days INTEGER DEFAULT 0,
    resting_hr INTEGER,
    hr_variability INTEGER,
    vo2max_estimate REAL,
    cadence_avg INTEGER,
    language TEXT DEFAULT 'en',
    communication_style TEXT DEFAULT 'casual',
    detail_level TEXT DEFAULT 'detailed',
    -- Location & Weather
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

-- ==========================================
-- INJURIES
-- ==========================================

CREATE TABLE injuries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    body_part TEXT NOT NULL,
    injury_type TEXT,                          -- shin_splints / runners_knee / itbs / plantar_fasciitis / achilles_tendinopathy
    description TEXT,
    severity TEXT DEFAULT 'mild',
    onset_date DATE,
    resolved_date DATE,
    active BOOLEAN DEFAULT 1,
    modified_training TEXT,                    -- "no speed work" / "reduced mileage 50%" / "pool running"
    source TEXT DEFAULT 'conversation',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- SHOES
-- ==========================================

CREATE TABLE shoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    name TEXT NOT NULL,
    type TEXT DEFAULT 'daily_trainer',         -- daily_trainer / speed / race / trail
    km_on_shoes REAL DEFAULT 0,
    added_date DATE DEFAULT (date('now')),
    retired BOOLEAN DEFAULT 0
);

-- ==========================================
-- RUNS
-- ==========================================

CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    run_date DATE DEFAULT (date('now')),
    run_type TEXT,                             -- easy / tempo / interval / long_run / recovery / race / other
    distance_km REAL,
    duration_sec INTEGER,                      -- total moving time
    avg_pace_sec_per_km REAL,                  -- seconds per km
    avg_hr INTEGER,
    max_hr INTEGER,
    cadence_avg INTEGER,
    elevation_gain_m INTEGER DEFAULT 0,
    rpe INTEGER,                               -- 1-10
    notes TEXT,
    shoe_id INTEGER REFERENCES shoes(id),
    -- Weather at run time
    weather_temp_c REAL,
    weather_condition TEXT,                    -- clear/rain/hot/windy/storm/cold
    weather_impact TEXT,                       -- AI: "Heat slowed pace ~5 sec/km"
    source TEXT DEFAULT 'manual',              -- manual / garmin / strava / screenshot
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- INTERVAL SPLITS (for track/speed sessions)
-- ==========================================

CREATE TABLE run_splits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id),
    split_number INTEGER,
    distance_m REAL,                           -- 400, 800, 1000
    duration_sec REAL,
    recovery_sec REAL
);

-- ==========================================
-- PERSONAL BESTS
-- ==========================================

CREATE TABLE personal_bests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    distance TEXT NOT NULL,                    -- 1k / 5k / 10k / half_marathon / marathon
    time_sec INTEGER NOT NULL,
    achieved_date DATE,
    run_id INTEGER REFERENCES runs(id),
    UNIQUE(chat_id, distance)
);

-- ==========================================
-- METRICS (time series)
-- ==========================================

CREATE TABLE metric_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    category TEXT NOT NULL,                    -- body / recovery / performance
    metric_name TEXT NOT NULL,                 -- weight_kg / sleep_hours / resting_hr / vo2max / weekly_km
    value REAL NOT NULL,
    unit TEXT,
    source TEXT DEFAULT 'manual',
    confidence REAL DEFAULT 1.0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- COACH OBSERVATIONS
-- ==========================================

CREATE TABLE coach_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    category TEXT NOT NULL,                    -- personality / motivation / pattern / preference
    observation TEXT NOT NULL,
    evidence TEXT,
    confidence INTEGER DEFAULT 1,
    first_observed DATE,
    last_observed DATE,
    active BOOLEAN DEFAULT 1
);

-- ==========================================
-- CONNECTED SERVICES
-- ==========================================

CREATE TABLE connected_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    service TEXT NOT NULL,                     -- garmin / strava
    connected BOOLEAN DEFAULT 0,
    scopes TEXT,                               -- JSON: ["activity","heart_rate"]
    token_encrypted TEXT,
    last_sync TIMESTAMP,
    last_sync_status TEXT,
    UNIQUE(chat_id, service)
);

-- ==========================================
-- MILESTONES
-- ==========================================

CREATE TABLE milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER REFERENCES runners(chat_id),
    milestone_type TEXT NOT NULL,              -- first_5k / first_10k / distance_pr / streak / total_km
    title TEXT NOT NULL,
    value TEXT,
    achieved_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TAGS
-- ==========================================

CREATE TABLE user_tags (
    chat_id INTEGER REFERENCES runners(chat_id),
    tag TEXT NOT NULL,
    UNIQUE(chat_id, tag)
);

-- ==========================================
-- INDEXES
-- ==========================================

CREATE INDEX idx_runs_chat ON runs(chat_id);
CREATE INDEX idx_runs_date ON runs(run_date);
CREATE INDEX idx_runs_type ON runs(run_type);
CREATE INDEX idx_metric_log_chat ON metric_log(chat_id);
CREATE INDEX idx_metric_log_name ON metric_log(metric_name);
CREATE INDEX idx_injuries_chat ON injuries(chat_id);
CREATE INDEX idx_shoes_chat ON shoes(chat_id);
CREATE INDEX idx_observations_chat ON coach_observations(chat_id);
CREATE INDEX idx_splits_run ON run_splits(run_id);
```

---

## Data Ingestion Flow

### Source Confidence Matrix

```
Source              | Confidence | Frequency    | Method
────────────────────┼───────────┼─────────────┼─────────────────
Garmin API          | ★★★★★     | Auto (daily) | OAuth2 + poll
Strava API          | ★★★★★     | Per run      | OAuth2 + webhook
Manual Log (/log)   | ★★★★☆     | Per run      | NLP parsing
Screenshot OCR      | ★★★☆☆     | On upload    | Vision AI
Conversation        | ★★☆☆☆     | Continuous   | Pattern matching
```

### Merge Rules

```
1. Garmin/Strava OVERRIDES manual for SAME run (API data is ground truth)
2. Manual OVERRIDES if no API data exists (or different run)
3. Screenshot → reviewed before commit (confidence < 0.9 asks user)
4. Conversation → inferred, flagged as low confidence, confirmed later
```

### Screenshot OCR Pipeline

Supports: Garmin Connect, Strava, Apple Fitness, Nike Run Club, adidas Running

```
User sends screenshot → Vision AI extracts:
  distance, duration, avg_pace, avg_hr, elevation, cadence
  → Match to known run type → Validate vs history → Save or confirm
```

---

## Conversation-Driven Profile Updates

```python
PATTERNS = {
    # Goal Change
    "I want to run a marathon": {"action": "update_goal", "value": "marathon"},
    "I just want to finish a 5K": {"action": "update_goal", "value": "finish_5k"},
    "I want to get faster at 5K": {"action": "update_goal", "value": "improve_5k"},
    
    # Injury
    "my shins hurt": {"action": "add_injury", "type": "shin_splints"},
    "knee pain on the outside": {"action": "add_injury", "type": "itbs"},
    "heel hurts in the morning": {"action": "add_injury", "type": "plantar_fasciitis"},
    
    # Schedule
    "I can only run 3 days now": {"action": "update_schedule", "days": 3},
    "I'm traveling next week": {"action": "update_note", "value": "travel_week"},
    
    # Shoe tracking
    "I got new shoes": {"action": "add_shoe", "follow_up": "What brand/model?"},
    
    # Fatigue
    "legs feel heavy today": {"action": "note_fatigue", "follow_up": "How's your sleep been?"},
    "I'm exhausted": {"action": "check_recovery", "follow_up": "Resting HR? Sleep hours?"}
}
```
