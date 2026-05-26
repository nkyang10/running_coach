# AI Running Coach

> Version: 1.0
> Target: Windows VM (no Docker)
> Managed via: OpenCode / Claude Code / Any AI Agent
> License: MIT (code), CC-BY-NC (knowledge templates)

A multi-runner AI coaching assistant with a curated running knowledge base.
Personalized training plans, injury-aware adaptation, Garmin/Strava integration,
and AI-driven self-improving quality control. Basic coaching is FREE forever.

## Quick Start

```powershell
python --version                  # ≥ 3.11
git clone <repo-url> coach
cd coach
python -m venv venv && .\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env            # fill in API keys
python scripts/seed_knowledge.py  # seed running knowledge
python main.py                    # start bot
```

## Documentation

| Doc | Purpose |
|---|---|
| `docs/ARCHITECTURE.md` | System design, components, data flow |
| `docs/IMPLEMENTATION_PLAN.md` | 7-phase build plan |
| `tests/test_plan.md` | 120+ test cases |
| `docs/GITHUB_WORKFLOW.md` | Issue → commit → auto-merge → deploy |
| `docs/QC_SYSTEM.md` | AI self-improving quality control |
| `docs/SERVER_GUIDE.md` | Server ops + auto-deploy agent |
| `docs/COMMERCIAL.md` | Free/Premium/Enterprise tiers |
| `docs/DATA_STRUCTURE.md` | Runner profile, DB schema, data flow |

## Knowledge Base (20 files)

```
knowledge/
├── training-philosophy.md        ← 80/20 polarized, consistency-first
├── workouts/                     ← easy, tempo, interval, long run, recovery, strides, hills
├── cross-training/               ← strength for runners, mobility, injury prevention
├── programs/                     ← couch-to-5k, 5k-improver, half-marathon
└── rules/                        ← pace zones, progression, deload/taper, injury guide, shoes
```

## Structure

```
coach/
├── app/           ← Core: bot.py, coach.py, database.py, knowledge.py, models.py
├── admin/         ← Telegram admin commands + system management
├── qc/            ← AI test agent + judge + self-improve engine
├── docs/          ← Full documentation
├── knowledge/     ← Curated running content (20 files)
├── tests/         ← Test plan + test KB fixtures
├── scripts/       ← Seed KB, seed test users, backup
└── .github/       ← CI/CD + issue templates
```
