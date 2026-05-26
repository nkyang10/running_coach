# AI Private Coach — GitHub Workflow

> Issue → Branch → Commit → PR → Merge → Deploy
> Every code change is traceable to a GitHub Issue.

---

## 1. Issue Templates

### Feature / Enhancement

```markdown
---
title: "[Feature] Add Romanian Deadlift to exercise library"
labels: enhancement, phase-3
assignees: ""
---

## Description
[Clear description of what's needed and why]

## Expected Behavior
- [Specific behavior 1]
- [Specific behavior 2]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Test: scenario description
- [ ] Test: scenario description

## Linked Issues
- Depends on: #N
- Related: #N
```

### Bug Fix

```markdown
---
title: "[Bug] /plan suggests box squat for patellar tendinitis"
labels: bug, safety
assignees: ""
---

## Description
[What's wrong and why it matters]

## Steps to Reproduce
1. Create user with injury=knee, severity=moderate
2. /plan
3. See "Box Squat 3x5" in output

## Expected
[What should happen instead]

## Root Cause
[File + reason]

## Fix
- [ ] Change 1
- [ ] Change 2
```

### QC Auto-Fix

```markdown
---
title: "[QC] Auto-fix: [description]"
labels: qc, auto-fix
assignees: ""
---

## Trigger
QC Run #[number] flagged: [scenario] scored [score]

## Judge Analysis
"[Judge's evaluation]"

## Auto-Fix Applied
- [file]: +N lines
- [change description]

## Verification
- QC re-run: [score]/100 ✅
- Regression check: all related scenarios pass ✅

## Files Changed
- M [file path]
```

---

## 2. Branch Naming Convention

```yaml
feature:  "feature/<issue-number>-<short-description>"
bugfix:   "fix/<issue-number>-<short-description>"
qc:       "qc/<issue-number>-<description>"
docs:     "docs/<issue-number>-<description>"
release:  "release/v<version>"

examples:
  - feature/42-add-romanian-deadlift
  - fix/58-box-squat-knee-injury
  - qc/92-auto-fix-fatigue-response
  - docs/101-api-reference
  - release/v1.2.0
```

---

## 3. Commit Message Convention

```yaml
format: "<type>(<scope>): <description> #<issue-number>"

types:
  feat:     "New feature or enhancement"
  fix:      "Bug fix"
  qc:       "QC auto-fix"
  docs:     "Documentation"
  test:     "Test addition/modification"
  refactor: "Code restructuring"
  kb:       "Knowledge base change"
  chore:    "Build, CI, config"

scopes:
  coach:    "app/coach.py — core logic"
  bot:      "app/bot.py — Telegram handlers"
  kb:       "knowledge/ — training content"
  db:       "app/database.py — data layer"
  admin:    "admin/ — system management"
  qc:       "qc/ — quality control"
  test:     "tests/ — test suite"
  ci:       ".github/ — CI/CD"

examples:
  "feat(coach): add RDL to plan generation for glute focus #42"
  "fix(kb): exclude box squat for knee injuries #58"
  "qc(coach): auto-patch fatigue response tone #92"
  "test(coach): add RDL scenarios for beginner vs advanced #42"
  "docs(readme): update setup instructions #101"
  "kb(exercise): add Bulgarian split squat technique guide"
  "ci: add QC workflow to hourly schedule"
```

---

## 4. Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    1. CREATE ISSUE                            │
│                                                              │
│  → Create Issue #42: "[Feature] Add Romanian Deadlift"      │
│  → Labels: enhancement, phase-3                              │
│  → Assign to project board                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    2. CREATE BRANCH                           │
│                                                              │
│  git checkout -b feature/42-add-romanian-deadlift            │
│  → Branch name references Issue #42                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    3. IMPLEMENT — Commit Every Sub-Step         │
│                                                              │
│  Rule: Commit after EVERY atomic change.                     │
│        No batching. Each file creation/edit is a commit.     │
│                                                              │
│  Step 3a: Create model + commit                               │
│  → touch app/models.py, write User + Injury classes          │
│  → git commit -m "feat(db): add User and Injury models #42"  │
│                                                              │
│  Step 3b: Create model test + commit                          │
│  → write tests/test_models.py, 14 test cases                 │
│  → git commit -m "test(db): add model validation tests #42"  │
│                                                              │
│  Step 3c: Create database module + commit                     │
│  → write app/database.py, init_tables + CRUD                 │
│  → git commit -m "feat(db): add SQLite init + CRUD ops #42"  │
│                                                              │
│  Step 3d: Create DB tests + commit                            │
│  → write tests/test_database.py, 21 test cases               │
│  → git commit -m "test(db): add database CRUD tests #42"     │
│                                                              │
│  Step 3e: Create bot handler + commit                         │
│  → write app/bot.py, /start + /help handlers                 │
│  → git commit -m "feat(bot): add /start and /help handlers #42"│
│                                                              │
│  Step 3f: Create bot tests + commit                           │
│  → write tests/test_bot.py, 7 test cases                     │
│  → git commit -m "test(bot): add bot handler tests #42"      │
│                                                              │
│  ✅ EVERY sub-step = 1 commit = 1 passing pytest              │
│  ✅ Commit frequency: ~6-12 commits per phase                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    4. PUSH + AUTO PR                           │
│                                                              │
│  git push origin feature/42-add-romanian-deadlift            │
│                                                              │
│  → GitHub auto-creates PR                                    │
│  → PR title: "[#42] Add Romanian Deadlift"                  │
│  → PR body: "Closes #42" + per-commit summary               │
│  → No human approval required                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    5. CI PASSES → AUTO-MERGE                   │
│                                                              │
│  GitHub Actions runs:                                        │
│  ├── pytest tests/ -v → ALL passed ✅                        │
│  ├── ruff check → no issues ✅                               │
│  ├── black --check → formatted ✅                            │
│  └── Coverage: no regression ✅                              │
│                                                              │
│  → All checks green → AUTO-MERGE to develop                  │
│  → No human approval. Tests ARE the gate.                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    6. AUTO-MERGE TO MAIN + DEPLOY              │
│                                                              │
│  → develop branch auto-merges to main daily (3 AM)           │
│  → Or: immediately if all CI + QC checks pass                │
│  → GitHub auto-closes Issue #42                              │
│  → Production webhook triggers deploy                        │
│  → Zero human touch                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    7. AUTO-DEPLOY + VERIFY                     │
│                                                              │
│  Production OpenCode:                                        │
│  ├── git pull → sees new commits                             │
│  ├── Pre-deploy tests                                        │
│  ├── Restart bot                                             │
│  ├── QC smoke test (5 scenarios) → pass ✅                   │
│  └── Admin notified: "✅ #42 deployed"                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. GitHub Actions CI

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio pytest-cov ruff black
      - run: pytest tests/ -v --cov=app --cov-report=term-missing
        env:
          COACH_TEST_MODE: 1
      - run: ruff check app/
      - run: black --check app/ tests/

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          curl -X POST ${{ secrets.PRODUCTION_WEBHOOK_URL }} \
            -H "Content-Type: application/json" \
            -H "X-Deploy-Token: ${{ secrets.DEPLOY_TOKEN }}" \
            -d '{"repo": "coach", "branch": "main", "commit": "${{ github.sha }}"}'
```

---

## 6. Label Strategy

```yaml
# Type
enhancement:     "New feature or improvement"
bug:             "Something isn't working"
qc:              "QC auto-generated issue"
docs:            "Documentation only"
refactor:        "Code improvement, no behavior change"

# Priority
critical:        "Blocks production — fix immediately"
high:            "Important, this phase"
medium:          "Nice to have, next phase"
low:             "When we have time"

# Phase
phase-1:         "Core infrastructure"
phase-2:         "Knowledge base"
phase-3:         "Coach engine"
phase-4:         "Logging & progress"
phase-5:         "Adaptive engine"
phase-6:         "Admin self-mod"
phase-7:         "Production hardening"

# Domain
area-coach:      "Core coach logic"
area-bot:        "Telegram interface"
area-knowledge:  "Knowledge base"
area-db:         "Database"
area-admin:      "Admin commands"
area-qc:         "Quality control"

# Safety
safety:          "Affects user safety — highest priority"
data-loss:       "Risk of losing user data"

# Status
good-first-issue:"Easy entry point for new dev"
needs-discussion:"Needs design decision first"
blocked:         "Waiting on another issue/PR"
```
