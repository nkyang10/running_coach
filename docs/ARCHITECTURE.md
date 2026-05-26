# AI Private Coach — System Architecture

> Version: 1.0
> Last Updated: 2026-05-27

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Private Coach                        │
├─────────────────────────────────────────────────────────────┤
│  • Admin curates knowledge → style consistency ✅            │
│  • AI generates personalized running plans from curated KB      │
│  • Runner reports results → system adapts                       │
│  • System self-modifies via admin AI instructions            │
│  • Basic coaching FREE forever                               │
│  • Multi-source input: text, screenshot, Garmin/Strava       │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| **No Docker** — pure Python | Windows VM constraint, simplicity |
| **SQLite** — no DB server | Zero config, file-based, single process |
| **File-based knowledge base** — markdown | AI-readable, human-readable, git-trackable |
| **python-telegram-bot** | Free, well-documented, async |
| **Curated KB, not web RAG** | Admin controls training style, no random data |
| **Single Python process** | Easy to debug, deploy, manage |
| **Git-based self-modification** | AI can commit, push, deploy via hooks |

## 2. System Architecture

```
┌──────────────┐
│   Telegram   │  ← python-telegram-bot (webhook polling)
│   Bot User   │
└──────┬───────┘
       │ webhook / polling
┌──────▼──────────────────────────────────────────────┐
│              Python Async App (main.py)               │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ bot.py   │  │ coach.py │  │ knowledge.py     │   │
│  │ handlers │──│ engine   │──│ KB loader+search │   │
│  └──────────┘  └────┬─────┘  └──────────────────┘   │
│                     │                                │
│  ┌──────────────────▼──────────────────────────┐    │
│  │              LLM (OpenAI/Anthropic API)      │    │
│  │  • Plan generation  • Log parsing           │
│  │  • Progress analysis • Conversation         │
│  │  • Injury detection • Shoe tracking         │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ database │  │ admin/   │  │ qc/              │   │
│  │ .py      │  │ commands │  │ test+judge+fix   │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
└──────┬──────────────────────┬───────────────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐   ┌─────────────────────┐
│   SQLite DB  │   │  Curated Knowledge   │
│  (user data) │   │  Base (markdown)     │
│              │   │                     │
│ users        │   │ knowledge/          │
│ profiles     │   │   philosophy.md     │ ← coaching style
│ sessions     │   │   exercise-library  │ ← exercise DB
│ metrics      │   │   programs/         │ ← program templates
│ logs         │   │   rules/            │ ← progression, injury
│ injuries     │   └─────────────────────┘
│ observations │
└──────────────┘
```

## 3. Data Ingestion Sources

```
Source              | Confidence | Frequency    | Method
────────────────────┼───────────┼─────────────┼─────────────────
Garmin API          | ★★★★★     | Auto (daily) | OAuth2 + poll
Strava API          | ★★★★★     | Per run      | OAuth2 + webhook
Manual Log (/log)   | ★★★★☆     | Per run      | NLP parsing
Screenshot OCR      | ★★★☆☆     | On upload    | Vision AI
Conversation        | ★★☆☆☆     | Continuous   | Pattern matching
Open-Meteo Weather  | ★★★★☆     | Per cronjob   | Free REST API (no key)
User Command        | ★★★★☆     | On command   | /metrics command

Merge Rules:
  1. Garmin/Strava OVERRIDES manual for same metric + time window
  2. Manual log OVERRIDES API for exercise-specific data
  3. Screenshot data is REVIEWED before commit (if confidence < 0.9)
  4. Conversation data is INFERRED, flagged low confidence
```

## 4. Core Data Flow

```
User: "/plan"

main.py:
  1. get chat_id from update.effective_user.id
  2. runner = await get_runner(chat_id)
  3. if not runner: await onboarding_flow(update)

  4. status = read_profile(chat_id)
  5. philosophy = read_knowledge("philosophy.md")
  6. rules = search_knowledge("progression", runner.level)

  7. prompt = f"""
     You are a running coach following these principles:
     {philosophy}

     Current runner:
     {status}

     Apply these rules:
     {rules}

     DO NOT add training advice outside the knowledge base.
     """

  8. plan = await llm.chat(prompt)
  9. await update.message.reply_text(plan)
  10. save_session(chat_id, plan)
```

## 5. Key Components

### Bot Layer (app/bot.py)
- Telegram message routing
- Command handlers: /start, /plan, /log, /status, /metrics, /history, /help
- Admin commands: /admin_status, /admin_knowledge, /admin_backup, /admin_reload
- Free-form message → AI intent classification

### Coach Engine (app/coach.py)

**Single source of truth for all plan generation.**
Both `/plan` (user request) and cronjob (auto-delivery) call the same function:

```python
async def generate_plan(chat_id: int) -> str:
    """Called by: /plan command handler AND cronjob scheduler.
    Same input (runner profile + KB + recent runs) → same output.
    No divergence — one function, two callers."""
```

- Run plan generation with context injection
- Log parsing (free-text → structured run data)
- Progress analysis and trend detection
- Adaptation logic (plateau, deload, taper, injury)
- Shoe mileage tracking + replacement reminders

### Cronjob Plan Delivery

```python
# APScheduler cron job — full conversation loop:

# ─── Step 1: Auto-push plan (e.g., daily at 6 AM) ───
async def auto_deliver_plan(chat_id: int):
    plan = await generate_plan(chat_id, weather=await get_weather(chat_id))
    await send_telegram(chat_id, plan)

# ─── Step 2: Follow-up after expected run time ───
async def auto_follow_up(chat_id: int):
    # Scheduled for e.g., 8 AM (2h after plan delivery)
    await send_telegram(chat_id,
        "🏃 How did today's run go? /log to record it, "
        "or just tell me how it felt."
    )

# ─── User request (same function, no weather needed) ───
async def plan_command(update, context):
    plan = await generate_plan(update.effective_user.id)
    await update.message.reply_text(plan)

# Cron schedule (per runner, based on their preferred_time):
#   6:00 AM → push plan
#   8:00 AM → follow-up "跑成點？"
#   9:00 PM → if no log today, gentle reminder
```

**Guarantee:** generate_plan() is identical for both paths.
Weather is an optional input — cronjob provides it, manual /plan doesn't need to.

### Weather Integration

```python
async def get_weather(chat_id: int) -> dict | None:
    """Fetch weather for runner's location. Returns None if no location set."""
    runner = await get_runner(chat_id)
    if not runner.location_city:
        return None

    # Free API: Open-Meteo (no API key, no rate limit, commercial OK)
    # https://open-meteo.com/
    url = f"https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": runner.location_lat,
        "longitude": runner.location_lon,
        "daily": ["temperature_2m_max", "precipitation_sum", "wind_speed_10m_max"],
        "timezone": runner.location_timezone or "auto"
    }

    return {
        "temp_high_c": 28,
        "rain_mm": 0,
        "wind_kmh": 12,
        "condition": "clear",  # Derived: clear/rain/hot/windy/storm
        "advice": "Warm day — hydrate well. No rain expected."  # AI-generated
    }
```

Weather affects plan generation:
- **Hot (>30°C):** Suggest early morning or evening. Reduce pace targets by 5-10 sec/km. Add hydration note.
- **Rain:** Suggest treadmill alternative if available. "Wear a cap, embrace it."
- **Windy:** Adjust pace expectations. "Effort over pace today."
- **Storm/typhoon:** Suggest indoor cross-training instead.
- **Cold (< 5°C):** Add warm-up emphasis. Layer clothing advice.
- **No data:** Skip weather notes. Plan is still valid.

Weather also affects result feedback when runner logs:
- **Hot day + slower pace:** "It was 32°C — pace naturally drops 5-10 sec/km in heat. Your effort was right on target."
- **Hot day + normal pace:** "Same pace as last week but in 32°C heat? That's a real improvement. Heat-adjusted, you're faster."
- **Perfect conditions + slower pace:** "Beautiful weather today. Pace was off — fatigue or just an off day?"
- **Windy + pace drop:** "12 km/h headwind today — that costs ~3-5 sec/km. Effort-level you were right where you should be."
- **Rain + logged run:** "Respect for getting out in the rain. Don't worry about pace — wet roads slow you down safely."
- **No weather data:** Skip weather commentary. Standard feedback only.

Weather is stored alongside each run for historical context:
```sql
-- Added to runs table:
weather_temp_c REAL,       -- temperature at run time
weather_condition TEXT,    -- clear/rain/hot/windy/storm/cold
weather_impact TEXT        -- AI-generated: "Heat likely slowed pace by ~5 sec/km"
```

### Knowledge Engine (app/knowledge.py)
- Loads all markdown from knowledge/ directory
- Cached in memory, refreshable via /admin_reload
- Keyword search within loaded knowledge
- No vector DB needed (KB is small enough for grep)

### Admin System (admin/)
- Knowledge base CRUD via Telegram
- System status, backup, reload
- Auto git commit on knowledge edits

### QC System (qc/)
- Test Agent: Simulates user via Telegram API
- Judge Agent: Evaluates responses (different model)
- Self-Improve: Auto-fix knowledge base, create PRs, rollback

## 6. Self-Modification System

```
Git Integration:
  - Entire coach/ directory IS a git repository
  - OpenCode / Claude Code works directly on the repo
  - Admin Telegram commands auto-commit after knowledge edits
  - git push to private GitHub for backup

Workflow:
  Human: "Add Bulgarian split squat"

  OpenCode:
    1. Reads docs/ARCHITECTURE.md + docs/SERVER_GUIDE.md
    2. Creates knowledge/exercise-library/split-squat.md
    3. Updates cross-references in programs/
    4. Adds test in tests/
    5. git add + git commit + git push
    6. Signals /admin_reload

  Bot Self-Modification (via Telegram):
    1. /admin_knowledge edit <file>
    2. Writes to knowledge/ file
    3. Auto-runs: git add . && git commit -m "admin: updated {filename}"
    4. Calls knowledge.reload()
    5. Confirms to admin
```

## 7. Application Startup Sequence

```
main.py startup (called by run.bat or Task Scheduler):

  1. Parse CLI args (--mode=development|production|test)
  2. Load .env with python-dotenv
  3. Determine mode: CLI arg > BOT_MODE env > default "development"
  4. If mode == "test" → run pytest and exit by returning pytest exit code

  5. Initialize logging (structlog → console + file)
     - development: log to console + data/logs/coach.log
     - production: log to file only

  6. Initialize database (app.database.init_tables)
     - Auto-creates all tables on first run
     - Idempotent: safe to call every startup

  7. Load knowledge base (app.knowledge.KnowledgeBase)
     - Reads all .md files from knowledge/ directory
     - Cached in memory
     - KB path: COACH_KNOWLEDGE_PATH env or default "knowledge/"

  8. Start Telegram bot (app.bot.start_bot)
     - Registers command handlers (/start, /plan, /log, etc.)
     - Registers admin command handlers
     - Begins polling (development) or webhook (production)
```

### Mode Configuration

| Mode | Telegram Token | AI API Key | Logging | Auto-restart | Purpose |
|---|---|---|---|---|---|
| `development` | Dev bot | Dev key | Console + file | No | Local testing with test users |
| `production` | Production bot | Production key | File only | Yes (Task Scheduler) | Real users |
| `test` | None (pytest) | Mock or test key | Console | N/A | CI/CD, pre-deploy check |

### Environment Variables

```
TELEGRAM_BOT_TOKEN=...       # Required
OPENAI_API_KEY=...           # Required
ADMIN_CHAT_IDS=12345,67890   # Required: comma-separated
BOT_MODE=development         # Optional: development|production|test
COACH_KNOWLEDGE_PATH=knowledge/  # Optional: override KB path
COACH_DB_PATH=data/coach.db      # Optional: override DB path
```
