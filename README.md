# AI Running Coach

A multi-runner AI coaching assistant with a curated running knowledge base. Generates personalized training plans via OpenAI, tracks progress, adapts to fatigue and injuries, and provides intelligent coaching through Telegram.

> Version: 1.0 | Target: Windows VM (no Docker) | License: MIT (code), CC-BY-NC (knowledge)

---

## Quick Start

```powershell
python --version                     # ≥ 3.11
git clone <repo-url> coach
cd coach
python -m venv venv && .\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env               # fill in TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, ADMIN_CHAT_IDS
python scripts/seed_knowledge.py     # seed 21 knowledge files
python main.py                       # start bot
```

For development with auto-restart:
```powershell
run.bat
```

---

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Onboarding: set name, level, goal, weekly km. Existing users see profile summary |
| `/help` | Show all available commands |
| `/plan` | Generate personalized weekly training plan via AI (respects injuries, fatigue, goal) |
| `/log` | Log a run (e.g., `/log 5k in 25min RPE 7`). NLP parsing auto-detects distance, time, RPE, type |
| `/status` | View progress: level, fatigue, consistency, streak, last 30 days summary |
| `/metrics` | Record body metrics (e.g., `/metrics weight 72`, `/metrics sleep 8`) |
| `/history` | Show last 10 runs with distance, pace, type, RPE |
| `/shoes` | Track shoes: `/shoes add "Nike Pegasus 40"`, `/shoes list`, `/shoes retire "name"` |

### Admin Commands (restricted to ADMIN_CHAT_IDS)

| Command | Description |
|---|---|
| `/admin_status` | System status: runner count, weekly runs, active injuries, KB files |
| `/admin_help` | List admin commands |
| `/admin_reload` | Reload knowledge base from disk (no restart needed) |
| `/admin_backup` | Create timestamped zip backup of knowledge/ + data/ + docs/ |
| `/admin_knowledge list` | List all knowledge files |
| `/admin_knowledge show <path>` | Show a knowledge file's content |
| `/admin_knowledge search <query>` | Search knowledge base content |
| `/admin_knowledge add <path> <content>` | Create a new knowledge file |
| `/admin_knowledge edit <path> <content>` | Update an existing knowledge file |
| `/admin_knowledge delete <path>` | Delete a knowledge file (with confirmation) |

### Conversation-Driven Updates

The bot understands natural language for common scenarios:
- **Injuries**: "my knee hurts", "my shins hurt"
- **Goals**: "I want to run a marathon", "training for a 5K"
- **Fatigue**: "legs feel heavy", "I'm exhausted"
- **Schedule**: "I can only run 3 days now"
- **Shoes**: "I got new shoes"

---

## Adaptive Engine

The system automatically monitors and adjusts training:

| Feature | Trigger | Action |
|---|---|---|
| High fatigue alert | Fatigue >= 4/5 | Suggests rest day |
| Intensity warning | 3+ runs at RPE 8+ | Suggests swapping hard day for recovery |
| Progression readiness | 3+ runs at RPE <= 4 | Suggests increasing distance or adding strides |
| Deload suggestion | Every 4th program week | 40-50% volume, no hard sessions |
| Plateau detection | Stagnant distance over 6 runs | Suggests workout variation |
| Missed sessions | Low 30-day consistency | Motivational message |
| Fatigue auto-adjust | Average RPE trend | Fatigue level adjusts up/down |

---

## Project Structure

```
coach/
├── app/                # Core application
│   ├── bot.py          # Telegram bot + all command handlers
│   ├── coach.py        # AI coach engine, plan generation, adaptation
│   ├── config.py       # .env loader + config validation
│   ├── database.py     # SQLite init + full CRUD (12 tables)
│   ├── knowledge.py    # Knowledge base loader, search, CRUD
│   ├── logger.py       # Structured logging with rotation
│   └── models.py       # Pydantic data models (11 entities)
├── admin/              # Admin system
│   ├── commands.py     # Admin command registration
│   ├── knowledge_manager.py  # KB formatting helpers
│   └── system_manager.py     # Status, backup, git commit
├── qc/                 # Quality control (stub)
├── knowledge/          # Curated running content (21 files)
│   ├── training-philosophy.md
│   ├── admin-guidelines.md
│   ├── workouts/       # 7 workout type guides
│   ├── cross-training/ # strength, mobility, injury prevention
│   ├── programs/       # couch-to-5k, 5k-improver, half-marathon
│   └── rules/          # pace zones, progression, deload/taper, injury, shoes, plateau
├── docs/               # Full documentation (7 docs)
│   ├── ARCHITECTURE.md
│   ├── DATA_STRUCTURE.md
│   ├── GITHUB_WORKFLOW.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── QC_SYSTEM.md
│   ├── COMMERCIAL.md
│   └── SERVER_GUIDE.md
├── tests/              # Test suite
│   ├── test_models.py      # 10 model validation test groups
│   ├── test_database.py    # 10 CRUD test groups
│   ├── test_knowledge.py   # 3 KB test groups
│   ├── test_coach.py       # Coach engine + adaptation tests
│   ├── test_admin_knowledge.py  # Admin KB CRUD tests
│   ├── conftest.py         # Shared fixtures
│   ├── fixtures/
│   │   ├── knowledge_sample/  # 9-file test KB
│   │   └── sample_logs.json   # 7 run parsing test cases
│   └── test_plan.md      # 230+ documented test cases
├── scripts/            # Utilities
│   ├── seed_knowledge.py       # Seed 21 knowledge files
│   ├── seed_test_kb.py         # Seed test KB fixtures
│   ├── create_test_users.py    # Create 5 test runners
│   └── backup.py               # CLI backup with rotation
├── .github/
│   ├── workflows/ci.yml        # CI: test, lint, auto-merge, deploy
│   └── ISSUE_TEMPLATE/         # bug, feature, qc-fix templates
├── main.py             # Entry point
├── run.bat             # Launcher with auto-restart
├── requirements.txt    # 15 Python dependencies
└── .env.example        # Environment template
```

---

## Knowledge Base

21 curated files covering running training methodology:

```
knowledge/
├── training-philosophy.md     ← 80/20 polarized, consistency-first
├── admin-guidelines.md        ← Rules for AI behavior
├── workouts/                  ← easy, tempo, interval, long run, recovery, strides, hills
├── cross-training/            ← strength for runners, mobility, injury prevention
├── programs/                  ← couch-to-5k, 5k-improver, half-marathon
└── rules/                     ← pace zones, progression, deload/taper, injury, shoes, plateau
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | — | Bot token from @BotFather |
| `OPENAI_API_KEY` | Yes | — | OpenAI API key (GPT-4o-mini for plans) |
| `ADMIN_CHAT_IDS` | Yes | — | Comma-separated Telegram chat IDs for admin |
| `BOT_MODE` | No | `development` | `development` / `production` / `test` |
| `COACH_DB_PATH` | No | `data/coach.db` | SQLite database path |
| `COACH_KNOWLEDGE_PATH` | No | `knowledge/` | Knowledge base directory |

---

## Tests

```powershell
pytest tests/ -v              # 140+ tests
pytest tests/ --cov=app       # with coverage
ruff check app/               # lint
black --check app/ tests/     # format
```

---

## CI/CD

GitHub Actions runs on push/PR to `develop` and `main`:
1. **test** — `pytest` + `ruff` + `black`
2. **auto-merge-develop** — Auto-merges PRs to develop
3. **auto-merge-main** — Auto-merges PRs to main
4. **deploy** — Webhook to production (only when `PRODUCTION_WEBHOOK_URL` is configured)

---

## Architecture Overview

```text
User (Telegram) → python-telegram-bot → CoachBot (handlers)
  → CoachEngine (AI plan gen) → OpenAI API
  → KnowledgeBase (curated KB) → markdown files
  → Database (SQLite) → 12 tables
  → Adaptive Engine → fatigue, plateau, deload detection
  → Admin System → status, backup, KB management
```
