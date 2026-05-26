# AI Private Coach — Implementation Plan

> Version: 1.0
> Last Updated: 2026-05-27
> Status: Not Started

## Phase Overview

| Phase | Name | Duration | Dependencies | Status |
|-------|------|----------|--------------|--------|
| 0 | Environment Setup | Day 1 | None | ⬜ |
| 1 | Core Infrastructure | Day 2-3 | Phase 0 | ⬜ |
| 2 | Knowledge Base System | Day 4-5 | Phase 1 | ⬜ |
| 3 | Coach Engine — Plan Generation | Day 6-8 | Phase 2 | ⬜ |
| 4 | Logging + Progress Tracking | Day 9-11 | Phase 3 | ⬜ |
| 5 | Adaptive Engine | Day 12-15 | Phase 4 | ⬜ |
| 6 | Admin Self-Modification | Day 16-18 | Phase 5 | ⬜ |
| 7 | Production Hardening | Day 19-21 | Phase 6 | ⬜ |

---

## Phase 0: Environment Setup (Day 1)

**Goal:** Working Python environment + git repo + test infrastructure skeleton

### Steps

1. Install Python 3.11+ on Windows
2. Clone the repo: `git clone <repo-url> coach && cd coach`
3. Create virtual environment: `python -m venv venv && .\venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. Copy `.env.example` → `.env` and fill in API keys
6. Create package init files: `touch app/__init__.py admin/__init__.py qc/__init__.py tests/__init__.py`
7. Seed test knowledge base: `python scripts/seed_test_kb.py`
8. Verify: `python -c "import pytest, telegram, openai, aiosqlite"` → no errors
9. `pytest tests/ -v` → "no tests ran" (test infrastructure ready, test code comes in later phases)
10. `git add . && git commit -m "phase-0: environment setup complete"`

### Deliverables
- ✅ Working Python environment with all dependencies installed
- ✅ .env configured with API keys
- ✅ Package structure ready (app/, admin/, qc/, tests/ all have __init__.py)
- ✅ Test infrastructure ready (pytest runs, conftest in later phase)
- ✅ Test knowledge base seeded at tests/fixtures/knowledge_sample/
- ✅ Master test plan at tests/test_plan.md (reference doc for all phases)

### Test Verification
```bash
pytest tests/ -v  # Should output: "no tests ran" (skeleton only)
```

---

## Phase 1: Core Infrastructure (Day 2-3)

**Goal:** Running bot that can receive messages, store users, handle basic commands

### Files to Create

| File | Purpose |
|---|---|
| `app/models.py` | All Pydantic data models |
| `app/config.py` | .env loader + config validation |
| `app/logger.py` | Structured logging setup |
| `app/database.py` | SQLite init + CRUD functions |
| `app/bot.py` | Telegram bot with /start + /help handlers |
| `main.py` | Entry point: initializes all components |
| `scripts/create_test_users.py` | Seed test users for manual testing |
| `tests/test_models.py` | Pydantic model validation tests |
| `tests/test_database.py` | SQLite CRUD tests |

### Data Models (app/models.py)

```python
# Core models:
User            # chat_id, name, level, goal, experience, equipment
Injury          # body_part, description, severity, active
Session         # chat_id, date, program_name, completed, RPE, fatigue
ExerciseLog     # session_id, exercise_name, sets, reps, weight, RIR
Metric          # chat_id, metric_name, value, unit, timestamp
KnowledgeDoc    # path, title, content, tags
```

### Database Tables

```sql
users, injuries, equipment, sessions, exercise_logs, metrics
```

(See `docs/DATA_STRUCTURE.md` for full schema)

### Key Behaviors

- `/start` → New user? Trigger onboarding (level, goal, equipment, injuries)
- `/start` → Existing user? Show greeting + last session summary
- `/help` → Show all available commands
- Admin commands only accessible by ADMIN_CHAT_IDS from .env

### Test Verification

```bash
pytest tests/test_models.py -v     # All model validations pass
pytest tests/test_database.py -v   # All CRUD operations pass
pytest tests/ -v --cov=app         # Coverage ≥ 80%
```

### Manual Verification

```bash
python main.py --mode=development
# Telegram: /start → onboarding questions
# Telegram: /help → command list
```

---

## Phase 2: Knowledge Base System (Day 4-5)

**Goal:** Admin can curate knowledge + AI can read and search it

### Files to Create/Update

| File | Purpose |
|---|---|
| `app/knowledge.py` | Load + search knowledge base |
| `admin/__init__.py` | Admin package init |
| `admin/knowledge_manager.py` | CRUD via Telegram (list, show, edit, add, delete) |
| `admin/commands.py` | Admin command registration |
| `knowledge/training-philosophy.md` | ← Admin fills in coaching style |
| `knowledge/admin-guidelines.md` | ← Rules for AI behavior |
| `knowledge/exercise-library/squat-variations.md` | Squat exercises |
| `knowledge/exercise-library/press-variations.md` | Press exercises |
| `knowledge/exercise-library/pull-variations.md` | Pull exercises |
| `knowledge/exercise-library/hinge-variations.md` | Hinge exercises |
| `knowledge/exercise-library/accessory-movements.md` | Accessory work |
| `knowledge/programs/beginner-linear-progression.md` | Beginner template |
| `knowledge/programs/intermediate-531.md` | Intermediate template |
| `knowledge/programs/advanced-daily-undulating.md` | Advanced template |
| `knowledge/rules/progression-rules.md` | When to add weight |
| `knowledge/rules/deload-rules.md` | When to deload |
| `knowledge/rules/injury-modifications.md` | Injury adjustments |
| `knowledge/rules/plateau-detection.md` | Stalled progress handling |
| `knowledge/README.md` | Guide for admin curators |
| `scripts/seed_knowledge.py` | Initialize sample knowledge base |
| `tests/test_knowledge.py` | Knowledge loader + search tests |
| `tests/test_admin_knowledge.py` | Admin CRUD tests |
| `tests/fixtures/knowledge_sample/` | Mini KB for testing |

### Key Behaviors

- `/admin_knowledge list` → Shows all files in knowledge/
- `/admin_knowledge show <file>` → Returns file content
- `/admin_knowledge edit <file>` → Reply with new content to replace
- `/admin_knowledge add <file>` → Reply with content to create new
- `/admin_knowledge delete <file>` → Confirm then delete
- Knowledge auto-loaded on startup, refreshable via `/admin_reload`
- Non-admin users cannot access any admin command

### Test Verification

```bash
pytest tests/test_knowledge.py -v
pytest tests/test_admin_knowledge.py -v
pytest tests/ -v --cov=app
```

### Manual Verification

```bash
/admin_knowledge list
/admin_knowledge show training-philosophy.md
/admin_knowledge edit training-philosophy.md
  → "I believe in progressive overload with compound lifts..."
/admin_knowledge show training-philosophy.md  # Verify updated
```

---

## Phase 3: Coach Engine — Plan Generation (Day 6-8)

**Goal:** AI generates personalized training plans based on user profile + knowledge base

### Files to Create/Update

| File | Purpose |
|---|---|
| `app/coach.py` | Core coaching logic — plan generation, prompt engineering |
| Update `app/bot.py` | Add /plan command handler |
| `tests/test_coach.py` | Plan generation tests |
| `tests/fixtures/sample_logs.json` | Test data for plan generation |

### Plan Generation Logic

```python
async def generate_plan(user, db, knowledge_base):
    1. Load user status from DB (level, goal, injuries, equipment, recent sessions)
    2. Load knowledge sections (philosophy + applicable rules + program template)
    3. Check adaptation (plateau detection, deload needed, progression)
    4. Build system prompt with ALL context
    5. LLM call → structured plan
    6. Validate output safety (no extreme volume/weights)
    7. Save pending session to DB
    8. Return formatted plan
```

### Key Behaviors

- `/plan` → Generates personalized training based on user profile
- Plan respects user level (beginner != advanced)
- Plan respects injuries (no squats if bad knee)
- Plan respects equipment availability
- Plan follows training philosophy from knowledge base
- Plan includes: exercises, sets, reps, rest periods, RPE targets
- Safety validation: reject extreme volume, weight, or frequency

### Test Cases

```
TC-COACH-001: Beginner plan has compound lifts only (3-5 exercises max)
TC-COACH-002: Advanced plan has more variety + accessory work
TC-COACH-003: Injured user (knee) → no squats, alternatives provided
TC-COACH-004: Limited equipment → only uses available gear
TC-COACH-005: Plan changes over consecutive days (progression)
TC-COACH-006: Same request → different plan (variation)
TC-COACH-007: Safety filter catches 7-days/week plan
TC-COACH-008: Safety filter catches >10 exercises/session
TC-COACH-009: Plan structure validated with snapshot test
```

---

## Phase 4: Logging + Progress Tracking (Day 9-11)

**Goal:** Users report results, system tracks progress, shows trends

### Files to Update

| File | Change |
|---|---|
| `app/coach.py` | Add log parsing + progress analysis |
| `app/bot.py` | Add /log, /status, /metrics, /history handlers |
| `tests/test_coach.py` | Add logging + progress test groups |
| `tests/fixtures/sample_logs.json` | Add more test fixtures |

### Key Behaviors

**/log**
- User sends: "Did 5x5 squat at 80kg, felt hard RPE 8"
- AI parses: exercise=back_squat, sets=5, reps=5, weight=80, rpe=8
- Saves to exercise_logs table
- Responds with summary + encouragement
- Handles vague input ("I did bench press") → asks for details

**/status**
- Loads metrics trends (last 30 days)
- Session completion rate
- Volume trend (this week vs last)
- AI-generated progress summary + recommendations

**/metrics**
- Records time-series data: body_weight, 1RM, waist, etc.
- Tracks trend over time
- /metrics body_weight 75 → records 75kg

**/history**
- Shows last 10 sessions with key stats
- Completion rate per week

### Test Cases

```
TC-LOG-001: "5x5 squat 80kg RPE 8" → parsed correctly
TC-LOG-002: "bench 3x10 at 60kg" → parsed correctly
TC-LOG-003: "I did some bench today" → asks for details
TC-LOG-004: "I benched 200kg for 20 reps" → flagged suspicious
TC-LOG-005: Empty log → friendly prompt
TC-MET-001: /metrics body_weight 75 → stored + trend
TC-MET-002: /metrics duplicate → new entry created
TC-STATUS-001: /status shows all sections
TC-STATUS-002: /status for new user → empty state handled
TC-HIST-001: /history returns last 10 sessions
```

---

## Phase 5: Adaptive Engine (Day 12-15)

**Goal:** System auto-adjusts training based on progress and feedback

### Files to Update

| File | Change |
|---|---|
| `app/coach.py` | Add adaptation logic |
| `tests/test_coach.py` | Add adaptation test groups |

### Adaptation Rules

**Progression Auto-Regulation**
- If RPE < 7 for 2+ sessions → increase weight 2.5kg (upper) / 5kg (lower)
- If RPE > 9 for 2+ sessions → reduce volume 1 set
- If fatigue ≥ 4 for 2+ sessions → suggest rest day

**Plateau Detection**
- 3+ sessions with no weight increase on main lift → detect plateau
- Suggest deload or program change
- Message: "Your squat has stalled. Consider a deload week."

**Deload Scheduling**
- Every 4-6 weeks → auto-suggest deload week
- Deload plan: ~50% volume of normal
- User can accept or decline
- After deload: reset to 90% of peak, fresh progression

**Program Transition**
- Beginner LP stalls → suggest intermediate program
- Based on duration + progress rate

### Test Cases

```
TC-ADAPT-001: 3 sessions RPE < 7 → next plan increases weight
TC-ADAPT-002: 3 sessions RPE > 9 → next plan decreases volume
TC-ADAPT-003: 4 weeks no progress → plateau detected
TC-ADAPT-004: Plateau triggers deload suggestion
TC-ADAPT-005: User accepts deload → 50% volume plan
TC-ADAPT-006: User declines → continue current plan
TC-ADAPT-007: After deload → fresh progression from 90%
TC-ADAPT-008: Consistent completion → positive reinforcement
TC-ADAPT-009: Missed sessions → motivational message
```

---

## Phase 6: Admin Self-Modification (Day 16-18)

**Goal:** Full admin control via Telegram + git + OpenCode integration

### Files to Create/Update

| File | Purpose |
|---|---|
| `admin/system_manager.py` | Status, backup, restart, git integration |
| Update `admin/commands.py` | Add system commands |
| `scripts/backup.py` | Manual backup script |
| `scripts/dev_workflow.py` | GitHub issue/PR helpers for OpenCode |

### Key Behaviors

**System Commands**
- `/admin_status` → Uptime, user count, session count, DB size, memory
- `/admin_backup` → Creates zip of data/ + knowledge/, saved to data/backups/
- `/admin_reload` → Reload knowledge base from disk (no restart)

**Git Integration**
- Knowledge edit auto-creates git commit with message format
- Commit message: `kb: update <filename> - <description>`
- OpenCode can clone repo, make changes, push, bot auto-updates

### Test Cases

```
TC-ADMIN-001: /admin_status shows correct system info
TC-ADMIN-002: /admin_backup creates valid zip
TC-ADMIN-003: /admin_reload refreshes knowledge
TC-ADMIN-004: Non-admin cannot access admin commands
TC-ADMIN-005: No info leakage in denied response
TC-ADMIN-006: Knowledge edit creates git commit
TC-ADMIN-007: Git commit message matches convention
TC-ADMIN-008: No commit on unchanged content
```

---

## Phase 7: Production Hardening (Day 19-21)

**Goal:** Reliable 24/7 operation

### Tasks

**Windows Service Setup**
1. Create `run.bat` launcher
2. Windows Task Scheduler: Start on boot, restart on crash
3. Auto-restart loop in main.py wrapper

**Logging**
- Log rotation (file doesn't grow infinitely)
- Separate log files: coach.log, errors.log, qc.log
- Admin notified on crash

**Security Hardening**
- SQL injection sanitization
- API keys not logged in plaintext
- User data isolation (User A cannot access User B)
- Rate limiting on API calls

**Health Monitoring**
- Hourly health check (can bot respond?)
- QC auto-run on deploy
- Telegram alert on critical failure

### Test Cases

```
TC-PROD-001: Bot reconnects after Telegram API timeout
TC-PROD-002: OpenAI timeout → fallback plan (basic template)
TC-PROD-003: SQLite locked → retry logic works
TC-PROD-004: Corrupt DB detected on startup
TC-PROD-005: Log rotation works
TC-PROD-006: SQL injection attempts sanitized
TC-PROD-007: User A cannot access User B's data
TC-PROD-008: Rate limiting prevents API abuse
```

---

## CI/CD Pipeline Setup

Created during Phase 6, refined through Phase 7:

```yaml
# .github/workflows/ci.yml
Triggers: push to develop/main, PR to develop/main
Jobs:
  - test: pytest + coverage + ruff + black
  - build: package artifact (main only)
  - deploy: webhook to production (main only)
```

```yaml
# .github/workflows/deploy.yml
Triggers: push to main
Jobs:
  - deploy: POST to production webhook URL
```

---

## QC System Setup

Created during Phase 3, refined through Phase 5-7:

```
qc/
├── test_agent.py     # AI user simulator
├── judge.py          # Response evaluator
├── self_improve.py   # Auto-fix engine
└── scheduler.py      # Cron jobs

Schedule:
  - Hourly: 2 quick scenarios, warn only
  - Daily (3 AM): Full 20-scenario run, auto-fix
  - Weekly (Mon 4 AM): Multi-model cross-validation
  - On deploy: 5-scenario smoke test, block if fail
```

(See `docs/QC_SYSTEM.md` for full details)
