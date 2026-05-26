# AI Private Coach — Server Operations Guide

> For AI Agents and Human Admins
> Target: Windows VM

---

## 1. System Requirements

```
OS:   Windows 10/11 Pro or Windows Server 2019+
CPU:  2 cores minimum
RAM:  4 GB minimum
Disk: 10 GB free
Net:  Internet (Telegram API + AI API + GitHub)

Software:
  Python 3.11+  (https://python.org — check "Add to PATH")
  Git           (https://git-scm.com — for source control)
```

---

## 2. First-Time Setup

```powershell
# 1. Verify Python
python --version
# Output: Python 3.11.x

# 2. Clone repository
cd C:\
git clone https://github.com/YOUR_ORG/coach.git
cd coach

# 3. Create virtual environment
python -m venv venv
.\venv\Scripts\activate
# You should see (venv) in your prompt

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
copy .env.example .env
# Edit .env with your credentials:
#   TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
#   OPENAI_API_KEY=sk-...
#   ADMIN_CHAT_IDS=123456789,987654321

# 6. Initialize database + seed knowledge
python scripts/seed_knowledge.py

# 7. Verify everything works
pytest tests/ -v

# 8. Start bot
python main.py
```

---

## 3. Daily Operations

### Starting / Stopping

```powershell
# Start (foreground — for testing)
cd C:\coach
.\venv\Scripts\activate
python main.py
# Press Ctrl+C to stop

# Start (background — for production)
# Use Windows Task Scheduler (see Section 5)
```

### Common Tasks

```powershell
# Check logs
type C:\coach\data\logs\coach.log
type C:\coach\data\logs\errors.log

# View database
sqlite3 C:\coach\data\coach.db
.tables
SELECT count(*) FROM users;
.quit

# Create backup
python scripts/backup.py
# → Creates data/backups/backup-YYYYMMDD.zip

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 4. Updating the System

### Via Git (recommended for code changes)

```powershell
cd C:\coach
git pull origin main
.\venv\Scripts\activate
pip install -r requirements.txt  # if requirements changed
# Restart bot
```

### Via Telegram (for knowledge base changes)

```
Send to bot:
  /admin_knowledge edit <filename>
  [new content]
  
The system auto-saves and reloads.
```

### Rollback

```powershell
# If something goes wrong:
cd C:\coach
git log --oneline -5           # See recent commits
git checkout <previous-commit> # Rollback
python main.py                 # Verify it works
git revert <bad-commit>        # Proper fix
```

---

## 5. Windows Task Scheduler Setup

### Create a Startup Task

1. Open **Task Scheduler** (Win+R → `taskschd.msc`)
2. Click **Create Task**
3. **General** tab:
   - Name: `AI Coach Bot`
   - Run whether user is logged on or not
   - Run with highest privileges
4. **Triggers** tab:
   - New → Begin the task: At startup
5. **Actions** tab:
   - New → Action: Start a program
   - Program: `C:\coach\run.bat`
6. **Settings** tab:
   - Allow task to be run on demand
   - If task fails, restart every 1 minute
   - Stop task if it runs longer than 3 days (restart for freshness)

### Create run.bat

```batch
@echo off
cd /d C:\coach
call .\venv\Scripts\activate
python main.py
```

---

## 6. Backup & Restore

### Automated Backup (Task Scheduler)

```powershell
# Create a daily backup task:
Trigger: Daily at 3:00 AM
Action: python C:\coach\scripts\backup.py
```

### Restore from Backup

```powershell
# 1. Stop bot
# 2. Restore files:
cd C:\coach
tar -xf data\backups\backup-20260526.zip
# 3. Start bot
```

### Backup Retention

```yaml
Daily backups: Keep 7 days (auto-cleanup in backup.py)
Weekly backups: Keep 4 weeks
Manual backups: Keep forever
```

---

## 7. Monitoring

### Health Check

The bot sends an alert to admin Telegram if:
- Python process crashes
- OpenAI/Anthropic API is unreachable
- Database is corrupt
- Disk space < 1GB
- QC score drops below threshold

### Logs

| File | Purpose | Retention |
|------|---------|-----------|
| `data/logs/coach.log` | All INFO+ messages | 7 days |
| `data/logs/errors.log` | WARNING+ messages only | 30 days |
| `data/logs/qc.log` | QC run results | 30 days |

### Log Rotation

Log files auto-rotate at 10MB. Max 5 rotated files per log.

---

## 8. Troubleshooting

| Problem | Check | Solution |
|---|---|---|
| Bot doesn't start | Token in .env? | Run: `python -c "import os; print('TELEGRAM_BOT_TOKEN' in open('.env').read())"` |
| "Module not found" | Virtual env active? | Run: `.\venv\Scripts\activate` then retry |
| DB errors | File permissions? | Check C:\coach\data\ directory exists |
| AI API errors | API key valid? | Check OPENAI_API_KEY in .env |
| Knowledge not updating | Forgot reload? | Send: `/admin_reload` to bot |
| Bot disconnected | Internet? | Test: `ping api.telegram.org` |
| Tests failing | Test KB exists? | Check `tests/fixtures/knowledge_sample/` |

---

## 9. Production Deployment Notes

```yaml
Environment variables:
  BOT_MODE=production          # Enables production settings
  TELEGRAM_BOT_TOKEN=...       # Production bot token (different from dev)
  OPENAI_API_KEY=...           # Production API key
  ADMIN_CHAT_IDS=...           # Your Telegram chat ID(s)

Security:
  - .env file must NOT be committed to git
  - Production bot has different token than dev bot
  - Admin commands restricted to ADMIN_CHAT_IDS
  - Rate limiting enabled (max 30 requests/min per user)

Monitoring:
  - Health check every hour
  - Admin alerted on crash
  - Logs rotated automatically
  - Daily backup at 3 AM
```

---

## 10. Production Auto-Deploy Agent

When a PR merges to `main` on GitHub, CI triggers a deploy webhook.
A second OpenCode instance on the production VM handles the entire deploy.

### Architecture

```
GitHub main merge
       │
       ▼
GitHub Actions → POST webhook → Production VM (port 9000)
       │
       ▼
┌─────────────────────────────────────────────────┐
│  OpenCode on Production VM                       │
│                                                  │
│  1. Receive webhook (repo=coach, branch=main)     │
│  2. git pull origin main                         │
│  3. pip install -r requirements.txt (if changed) │
│  4. pytest tests/ -v (pre-deploy check)          │
│  5. If tests fail → ROLLBACK + alert admin       │
│  6. Stop current bot process                     │
│  7. Start new bot via run.bat                     │
│  8. Health check (wait 5s, verify bot online)    │
│  9. Notify admin Telegram with changelog         │
└─────────────────────────────────────────────────┘
```

### Deploy Sequence (Detailed)

```
Step 1: Webhook received
  POST /deploy
  Headers: X-Deploy-Token: <secret>
  Body: {"repo": "coach", "branch": "main", "commit": "abc123"}

Step 2: git pull
  cd C:\coach && git pull origin main
  If "Already up to date" → skip deploy, log nothing changed

Step 3: Update dependencies
  .\venv\Scripts\pip install -r requirements.txt

Step 4: Pre-deploy tests
  .\venv\Scripts\python -m pytest tests/ -v --timeout=30
  If exit code != 0 → ROLLBACK: git checkout HEAD~1
  → Send Telegram alert: "❌ Deploy blocked: tests failed"

Step 5: Stop current bot
  taskkill /F /IM python.exe /FI "WINDOWTITLE eq coach*"
  Wait 2s for clean shutdown (sessions saved)

Step 6: Show changelog
  git log --oneline -5 (shows what changed)
  Included in deploy notification

Step 7: Start new bot
  start "coach-bot" C:\coach\run.bat

Step 8: Health check
  Wait 5 seconds
  Send /admin_status to bot → verify response
  If no response after 3 retries → ROLLBACK

Step 9: Notify admin
  Telegram: "✅ Deployed: abc123
  Changes:
  - feat: add Romanian deadlift #42
  - fix: knee injury safety #58"
```

### Webhook Listener Setup

```powershell
# On production VM, run once:
cd C:\coach
# The deploy agent listens on port 9000
# Run via Task Scheduler: "At startup" trigger
# Script: deploy_agent.py in production mode
```

### Rollback Rules

| Failure Point | Action |
|---|---|
| Tests fail (pre-deploy) | `git checkout HEAD~1`, alert admin |
| Health check fail (post-deploy) | `git checkout HEAD~1`, restart old version |
| Bot crashes within 5 min | Auto-detect via health monitor, auto-rollback |
| QC score drops (post-deploy) | QC hourly run detects, auto-rollback if < 30 |

### Deploy Log

All deploys logged to `data/logs/deploy.log`:
```
2026-05-27 14:30 | abc123 | DEPLOY_START | commit: feat: add RDL #42
2026-05-27 14:30 | abc123 | GIT_PULL    | Fast-forward main abc123..def456
2026-05-27 14:30 | abc123 | PIP_INSTALL | Requirements unchanged
2026-05-27 14:31 | abc123 | TESTS       | 127 passed, 0 failed ✅
2026-05-27 14:31 | abc123 | STOP_BOT    | Process 12345 killed
2026-05-27 14:31 | abc123 | START_BOT   | Process 12346 started
2026-05-27 14:31 | abc123 | HEALTH      | Bot responding ✅
2026-05-27 14:31 | abc123 | NOTIFY      | Admin notified
2026-05-27 14:31 | abc123 | DEPLOY_OK   | ✅ Success
```

### Integration with CI

```
# .github/workflows/ci.yml (existing) triggers:
curl -X POST ${{ secrets.PRODUCTION_WEBHOOK_URL }} \
  -H "Content-Type: application/json" \
  -H "X-Deploy-Token: ${{ secrets.DEPLOY_TOKEN }}" \
  -d '{"repo": "coach", "branch": "main", "commit": "${{ github.sha }}"}'

# Production OpenCode receives this and executes the deploy sequence above.
# Both sides documented here → AI agent on either machine can understand the full flow.
```
