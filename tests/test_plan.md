# AI Running Coach — Master Test Plan

> **Living document.** Every phase updates this.
> Run: `pytest tests/ -v`
> Coverage: `pytest tests/ --cov=app --cov-report=term-missing`

---

## Test Configuration

```yaml
Framework: pytest + pytest-asyncio + pytest-cov + pytest-mock
Fixtures: tests/conftest.py
Test KB: tests/fixtures/knowledge_sample/
Mock LLM: Yes (all unit tests), Real LLM optional (COACH_USE_REAL_LLM=1)
```

---

## Phase 0: Environment Setup ✅

- [x] Python 3.11+ available
- [x] All pip packages installable
- [x] .env template validates
- [x] Git repository initialized
- [x] Test infrastructure runs: `pytest tests/ -v`

## Phase 1: Core Infrastructure 🟡

### Test Group 1.1: Data Models
```
TC-MODEL-001: Runner model validates required fields (chat_id, level, goal)
TC-MODEL-002: Runner model rejects invalid level
TC-MODEL-003: Runner model rejects invalid goal
TC-MODEL-004: Run model validates distance > 0
TC-MODEL-005: Run model validates avg_pace within realistic range (3:00-10:00/km)
TC-MODEL-006: Run model validates RPE 1-10
TC-MODEL-007: Shoe model tracks km and retirement
TC-MODEL-008: PersonalBest model stores time_sec correctly
TC-MODEL-009: Injury model defaults to active=True
TC-MODEL-010: All models serialize/deserialize correctly
```

### Test Group 1.2: Database
```
TC-DB-001: init_tables() creates all tables
TC-DB-002: init_tables() is idempotent
TC-DB-003: create_runner() inserts new runner
TC-DB-004: create_runner() raises on duplicate chat_id
TC-DB-005: get_runner() returns correct runner
TC-DB-006: get_runner() returns None for unknown ID
TC-DB-007: update_runner() modifies fields
TC-DB-008: create_injury() links to runner
TC-DB-009: get_active_injuries() returns active only
TC-DB-010: create_run() stores all fields (distance, pace, HR, RPE)
TC-DB-011: get_recent_runs() returns last N days
TC-DB-012: create_shoe() tracks km
TC-DB-013: update_shoe_km() increments mileage
TC-DB-014: warn_shoe_threshold() triggers at 400km
TC-DB-015: create_personal_best() records PB
TC-DB-016: get_personal_bests() returns sorted by distance
TC-DB-017: create_metric() records time series
TC-DB-018: get_metrics_trend() returns sorted by date
TC-DB-019: Database handles concurrent writes safely
TC-DB-020: Delete runner cascades correctly
```

### Test Group 1.3: Bot Startup
```
TC-BOT-001: main.py initializes without errors
TC-BOT-002: Bot registers all command handlers
TC-BOT-003: Invalid token shows clear error
TC-BOT-004: /help returns command list
TC-BOT-005: /start triggers onboarding for new runner
TC-BOT-006: /start shows summary for existing runner
TC-BOT-007: Unknown command shows help suggestion
```

## Phase 2: Knowledge Base 🟡

### Test Group 2.1: Knowledge Loader
```
TC-KB-001: load_knowledge_base() loads all .md files
TC-KB-002: Returns correct structure (philosophy, workouts, programs, rules)
TC-KB-003: Handles empty directory gracefully
TC-KB-004: Handles missing directory gracefully
TC-KB-005: Caching works correctly
TC-KB-006: search_knowledge() finds by keyword
TC-KB-007: search_knowledge() filters by section
TC-KB-008: Returns empty for no match
TC-KB-009: reload_knowledge() refreshes from disk
TC-KB-010: Malformed markdown doesn't crash loader
```

### Test Group 2.2: Admin Knowledge CRUD
```
TC-ADMIN-KB-001: /admin_knowledge list shows all files
TC-ADMIN-KB-002: /admin_knowledge show returns content
TC-ADMIN-KB-003: /admin_knowledge show invalid returns error
TC-ADMIN-KB-004: /admin_knowledge edit overrides file
TC-ADMIN-KB-005: /admin_knowledge edit creates file if new
TC-ADMIN-KB-006: Triggers KB reload + git commit
TC-ADMIN-KB-007: /admin_knowledge add creates file
TC-ADMIN-KB-008: /admin_knowledge delete removes file
TC-ADMIN-KB-009: Non-admin denied access
```

## Phase 3: Coach Engine 🟡

### Test Group 3.1: Plan Generation
```
TC-COACH-001: generate_plan() returns valid output for new runner (couch-to-5k)
TC-COACH-002: generate_plan() returns 5K improver plan for intermediate
TC-COACH-003: generate_plan() returns HM plan for half-marathon goal
TC-COACH-004: Plan respects injury restrictions (no speed work for shin splints)
TC-COACH-005: Plan respects weekly mileage limit (10% rule)
TC-COACH-006: Plan uses knowledge base content only (no random advice)
TC-COACH-007: Plan structure: run type, distance, pace guidance, RPE target
TC-COACH-008: Plan includes cross-training when appropriate
TC-COACH-009: Plan includes warm-up/cool-down notes
TC-COACH-010: LLM fallback works when primary API fails
TC-COACH-011: Plan changes week-over-week (progression)
TC-COACH-012: Same request + same state → different weekly schedule (variation)
TC-COACH-013: New runner gets walk-run, advanced gets structured workouts
TC-COACH-014: 80/20 rule enforced (80% easy mileage in plan)
```

### Test Group 3.2: Safety Validation
```
TC-SAFE-001: Rejects plan with >10% weekly mileage increase
TC-SAFE-002: Rejects speed work for runner with < 3 months experience
TC-SAFE-003: Rejects plan with no rest days (7 days/week)
TC-SAFE-004: Long run ≤ 30% of weekly mileage
TC-SAFE-005: No intervals for shin splints injury
TC-SAFE-006: Warning when HR zone distribution is off
TC-SAFE-007: No back-to-back hard days
```

## Phase 4: Logging & Progress 🟡

### Test Group 4.1: Run Logging
```
TC-LOG-001: "Ran 5K in 28:30, felt good" → parsed correctly
TC-LOG-002: "Easy 8K, 6:15/km, avg HR 145" → parsed
TC-LOG-003: "10K tempo, 5:00 pace, last 2K at 4:30" → parsed with splits
TC-LOG-004: "Did intervals: 6x400 at 4:00/km" → split recording
TC-LOG-005: "I ran today" → asks for details
TC-LOG-006: "Ran 42K in 1:30" → flagged as world-record suspicious
TC-LOG-007: Empty string → friendly prompt
TC-LOG-008: Gibberish → polite rephrase request
TC-LOG-009: Typos "tempoo run" → fuzzy matched to tempo
TC-LOG-010: Log updates weekly mileage counter
```

### Test Group 4.2: Progress Tracking
```
TC-STATUS-001: /status shows 30-day trends
TC-STATUS-002: /status shows weekly mileage trend
TC-STATUS-003: /status shows pace improvement
TC-STATUS-004: /status for new runner → "No data yet"
TC-STATUS-005: /status detects PB and celebrates
TC-METRIC-001: /metrics weight 68 → recorded
TC-METRIC-002: /metrics sleep 7.5 → recorded
TC-METRIC-003: /metrics duplicate → new time-series entry
TC-HISTORY-001: /history returns last 10 runs
TC-HISTORY-002: /history shows per-run stats
TC-HISTORY-003: /history for new runner → empty state
```

## Phase 5: Adaptive Engine 🟡

### Test Group 5.1: Progression
```
TC-ADAPT-001: 3 weeks consistent → mileage increases per 10% rule
TC-ADAPT-002: Elevated RHR → suggests reduced load
TC-ADAPT-003: Consistent pace improvement → positive reinforcement
TC-ADAPT-004: Missed runs → motivational message
TC-ADAPT-005: Build → Build → Build → Down week pattern
```

### Test Group 5.2: Fatigue & Recovery
```
TC-FAT-001: "Legs feel heavy" + sleep < 6 hrs → suggests recovery day
TC-FAT-002: Resting HR elevated 5+ bpm → flags overtraining risk
TC-FAT-003: Conversation fatigue pattern detected → stored as observation
TC-FAT-004: User reports fatigue → asks about sleep + RHR
```

### Test Group 5.3: Deload / Taper
```
TC-DEL-001: Week 4 of build → auto-suggest down week
TC-DEL-002: Down week: 60-70% of peak mileage
TC-DEL-003: User accepts → reduced plan generated
TC-DEL-004: User declines → continue current plan
TC-TAP-001: Race in 2 weeks → taper starts
TC-TAP-002: Race week → 50% volume, no hard sessions
```

### Test Group 5.4: Shoe Tracking
```
TC-SHOE-001: /shoes add "Nike Pegasus" → shoe created
TC-SHOE-002: Run logged → shoe km auto-incremented
TC-SHOE-003: Shoe hits 400 km → warning sent
TC-SHOE-004: Shoe hits 500 km → replacement recommended
TC-SHOE-005: /shoes list → shows all shoes with km
TC-SHOE-006: /shoes retire → marks retired
```

## Phase 6: Admin Self-Modification 🟡

```
TC-SYS-001: /admin_status returns correct system info
TC-SYS-002: /admin_backup creates valid zip
TC-SYS-003: /admin_reload refreshes knowledge
TC-SYS-004: Non-admin blocked from admin commands
TC-GIT-001: Knowledge edit → git commit
TC-GIT-002: Commit message matches convention
```

## Phase 7: Production Hardening 🟡

```
TC-RESIL-001: Bot reconnects after Telegram timeout
TC-RESIL-002: API timeout → fallback response
TC-RESIL-003: SQLite locked → retry with backoff
TC-RESIL-004: Corrupt DB detected → alert admin
TC-RESIL-005: Log rotation works
TC-SEC-001: Admin commands restricted to ADMIN_CHAT_IDS
TC-SEC-002: Runner A cannot access Runner B's data
TC-SEC-003: API keys not logged
```

---

## Test Fixture Design

### Database Fixtures
```python
# In-memory SQLite. Every test gets fresh isolated DB.
# test_db: empty DB with all tables
# seeded_db: pre-populated with 3 runners:
#   90001: New runner, couch-to-5k goal
#   90002: Intermediate, 5K improver, shin splints (active)
#   90003: Advanced, half marathon goal
```

### Test KB Content (tests/fixtures/knowledge_sample/)
```
tests/fixtures/knowledge_sample/
├── training-philosophy.md     ← 80/20 polarized
├── workouts/easy-run.md + tempo-run.md
├── programs/couch-to-5k.md + 5k-improver.md
├── rules/pace-zones.md + progression-rules.md + injury-guide.md
```

### Mock LLM Response Format
```python
{
    "plan": "Mon: Easy 5K. Tue: Tempo 20 min. Wed: Rest. ...",
    "runs": [
        {"day": "Mon", "type": "easy", "distance_km": 5, "pace_guide": "6:30-7:00/km"},
        {"day": "Tue", "type": "tempo", "duration_min": 20, "pace_guide": "5:15-5:30/km"}
    ],
    "notes": "Focus on keeping easy days truly easy. RPE 3-4."
}
```

### Test Runner Profiles
```
| chat_id | Name  | Level        | Goal         | Injuries           |
|---------|-------|--------------|--------------|--------------------|
| 90001   | Alice | new          | finish_5k    | None               |
| 90002   | Bob   | intermediate | improve_5k   | Shin splints (mild)|
| 90003   | Carol | advanced     | half_marathon| None               |
```

---

## Running Tests
```bash
pytest tests/ -v                                    # Full suite
pytest tests/ --cov=app --cov-report=term-missing   # With coverage
pytest tests/ -k "Phase1" -v                         # Specific phase
COACH_USE_REAL_LLM=1 pytest tests/test_coach.py -v   # Real LLM
```
