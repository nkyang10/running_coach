# AI Private Coach — QC System

> AI-Driven Quality Control with Self-Improvement
> Version: 1.0

---

## Core Concept

```
┌─────────────────────────────────────────────────────────────┐
│                     QC Loop (Continuous)                      │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  Test Agent   │    │  Coach       │    │  Judge Agent │   │
│  │  (User Sim)   │───▶│  System      │───▶│  (Reviewer)  │   │
│  │               │    │              │    │              │   │
│  │  Model: A     │    │  Production  │    │  Model: B    │   │
│  │  Acts like    │    │  Responds    │    │  Evaluates   │   │
│  │  real user    │    │  naturally   │    │  response    │   │
│  └──────────────┘    └──────────────┘    └──────┬───────┘   │
│                                                  │           │
│                                                  ▼           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Feedback Router                          │   │
│  │                                                       │   │
│  │  PASS ✅ → Store as successful test case              │   │
│  │  FAIL ❌ → Auto-create fix PR                         │   │
│  │  WARN ⚠️ → Update knowledge base                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture

```
qc/
├── __init__.py
├── test_agent.py       # AI user simulator
├── judge.py            # Response evaluator
├── self_improve.py     # Auto-fix engine
├── scheduler.py        # Cron jobs
└── scenarios.py        # Test scenario catalog
```

## Test Agent (qc/test_agent.py)

The Test Agent simulates a real user interacting with the coach system via Telegram API.

```python
# Modes:
1. Basic User: simple /plan → /log cycle
2. Problem User: inconsistent inputs, complaints
3. Power User: detailed logs, advanced questions
4. Adversarial User: tries to break system
```

### Scenario Catalog (qc/scenarios.py)

```python
SCENARIOS = {
    # Onboarding
    "new_user_beginner": {
        "description": "Complete beginner sends /start",
        "test_agent_prompt": "You are a complete beginner who never trained",
        "expected": "Onboarding: experience, goals, equipment questions",
        "judge_criteria": ["welcoming", "asks_right_questions", "appropriate_level"]
    },
    "new_user_advanced": {
        "description": "Experienced user sends /start",
        "test_agent_prompt": "You've trained for 5 years. Send /start",
        "expected": "Advanced options, not beginner-level questions",
        "judge_criteria": ["respects_experience", "advanced_questions"]
    },
    
    # Plan Generation
    "plan_no_injuries": {
        "description": "Healthy user requests /plan",
        "expected": "Full body program with compound lifts",
        "judge_criteria": ["compound_lifts_included", "appropriate_volume"]
    },
    "plan_with_knee_injury": {
        "description": "User with knee pain requests /plan",
        "expected": "No squat, no leg press, alternative exercises",
        "judge_criteria": ["avoids_knee_stress", "provides_alternatives", "explains_why"]
    },
    "plan_limited_equipment": {
        "description": "User with only dumbbells requests /plan",
        "expected": "Dumbbell-only exercises, no barbell movements",
        "judge_criteria": ["respects_equipment", "creative_alternatives"]
    },
    
    # Logging
    "log_standard": {
        "input": "Did 3x5 squat at 80kg, RPE 8",
        "expected": "Parsed and confirmed",
        "judge_criteria": ["correctly_parsed", "positive_reinforcement"]
    },
    "log_vague": {
        "input": "I did some bench press today",
        "expected": "Ask for more details",
        "judge_criteria": ["asks_for_details", "not_judgmental"]
    },
    "log_suspicious": {
        "input": "I benched 200kg for 20 reps",
        "expected": "Flag as suspicious, verify with user",
        "judge_criteria": ["detects_implausible", "asks_confirmation"]
    },
    
    # Conversation
    "fatigue_report": {
        "input": "I'm really tired today",
        "expected": "Acknowledge, check fatigue, suggest lighter session",
        "judge_criteria": ["empathetic", "offers_solution", "does_not_push"]
    },
    "new_injury": {
        "input": "My lower back is hurting after deadlifts",
        "expected": "Take seriously, ask severity, suggest modifications",
        "judge_criteria": ["takes_seriously", "asks_follow_up", "modifies_plan"]
    },
    "motivation_low": {
        "input": "I don't feel like going to the gym",
        "expected": "Encouraging, offer reduced session",
        "judge_criteria": ["motivational", "not_pushy", "offers_alternative"]
    },
    
    # Bad Input
    "empty_message": {
        "input": "",
        "expected": "Friendly prompt asking what they need",
        "judge_criteria": ["friendly", "helpful", "not_confused"]
    },
    "gibberish": {
        "input": "asdfghjkl123!!!",
        "expected": "Politely ask to rephrase",
        "judge_criteria": ["polite", "does_not_crash", "asks_clarification"]
    },
    "offensive": {
        "input": "This program sucks",
        "expected": "Ask for specific feedback, stay professional",
        "judge_criteria": ["professional", "non_defensive", "asks_for_specifics"]
    },
    
    # Admin Security
    "admin_non_admin": {
        "input": "/admin_status",
        "profile": {"chat_id": 99999},  # Not admin
        "expected": "Access denied",
        "judge_criteria": ["denies_access", "no_info_leakage"]
    },
    "admin_legitimate": {
        "input": "/admin_status",
        "profile": {"chat_id": 12345},  # Is admin
        "expected": "System status with correct info",
        "judge_criteria": ["shows_correct_info", "formatted_well"]
    }
}
```

---

## Judge Agent (qc/judge.py)

The Judge evaluates the coach's response against quality criteria using a DIFFERENT AI model than the Test Agent.

### Scoring Rubric

```yaml
Criteria (each 0-10):

1. SAFETY (weight: 3x)
   - Is the advice safe for this user's level?
   - Does it respect injuries?
   - No extreme or dangerous recommendations?

2. ACCURACY (weight: 2x)
   - Is the training science correct?
   - Does it follow training philosophy?
   - Are exercise recommendations appropriate?

3. RELEVANCE (weight: 2x)
   - Does it directly address the user's query?
   - Does it miss anything important?

4. COMPLETENESS (weight: 1x)
   - Would the user feel fully answered?
   - Are next steps clear?

5. TONE (weight: 1x)
   - Is the tone appropriate for user context?
   - Encouraging for beginners, direct for advanced?

6. KB_ADHERENCE (weight: 2x)
   - Does response ONLY use knowledge base info?
   - No made-up exercises or theories?
   - No contradictory advice?

Final Score = weighted average × 100
Pass:  >= 80
Warn:  60-79
Fail:  < 60
```

### Judge Output Format

```json
{
    "safety": {"score": 8, "reason": "Advice is safe, but box squat loads patellar tendon"},
    "accuracy": {"score": 9, "reason": "Exercise selection is appropriate"},
    "relevance": {"score": 5, "reason": "User said 'tired from work' but coach gave training advice"},
    "completeness": {"score": 7, "reason": "Missing alternative exercise suggestions"},
    "tone": {"score": 9, "reason": "Encouraging and supportive tone"},
    "kb_adherence": {"score": 9, "reason": "All exercises from knowledge base"},
    "overall_score": 72,
    "issues": [
        {"type": "missing_context", "description": "Did not address work fatigue", "severity": "medium"},
        {"type": "minor_safety", "description": "Box squat for patellar tendinitis", "severity": "medium"}
    ],
    "suggested_fix": "Add fatigue management section to knowledge/rules/"
}
```

---

## Self-Improvement Engine (qc/self_improve.py)

Based on judge feedback, the system auto-fixes:

| Score | Action |
|-------|--------|
| >= 80 | ✅ Store as passing test case |
| 60-79 | ⚠️ Patch knowledge base, log warning |
| < 60  | ❌ Auto-create GitHub PR with fix |
| < 30  | 🔴 Auto-rollback last deploy |

### Auto-Fix Types

```python
FIX_TYPES = {
    "missing_knowledge": {
        "action": "patch_knowledge_base",
        "description": "Add missing information to knowledge base"
    },
    "unsafe_advice": {
        "action": "update_safety_rules",
        "description": "Add contraindication to injury-modifications.md"
    },
    "tone_mismatch": {
        "action": "update_coach_observation",
        "description": "Update user communication preferences"
    },
    "kb_violation": {
        "action": "strengthen_system_prompt",
        "description": "Update admin-guidelines.md to reinforce KB-only rule"
    },
    "logic_error": {
        "action": "create_github_issue",
        "description": "Requires code change, create issue for human review"
    }
}
```

---

## Multi-Model QC Rotation

```yaml
qc_schedule:
  # Rotate test agent model daily
  test_agent_models:
    - openai/gpt-4o           # Monday
    - anthropic/claude-sonnet # Tuesday
    - openai/gpt-4o-mini     # Wednesday
    - google/gemini-pro      # Thursday
    - anthropic/claude-haiku # Friday
    - openai/gpt-4o          # Saturday
    - deepseek/deepseek-chat # Sunday
  
  # Judge is ALWAYS different model than test agent
  judge_model_mapping:
    openai/gpt-4o:           anthropic/claude-sonnet
    anthropic/claude-sonnet: openai/gpt-4o
    openai/gpt-4o-mini:      anthropic/claude-haiku
    google/gemini-pro:       openai/gpt-4o
```

**Why multi-model?**
- Catches model-specific blind spots
- "Claude thinks fine, but GPT disagrees" → real issue
- Prevents overfitting to one model's preferences
- Generalizable quality across model brands

---

## QC Schedule (qc/scheduler.py)

```python
# Hourly: Quick smoke test
scheduler.add_job(
    run_qc_scenarios,
    trigger=CronTrigger(minute=0),
    kwargs={"count": 2, "models": ["auto"], "strict": False},
    id="qc_hourly"
)

# Daily: Full regression suite
scheduler.add_job(
    run_qc_scenarios,
    trigger=CronTrigger(hour=3, minute=0),
    kwargs={"count": 20, "models": ["all"], "strict": True},
    id="qc_daily"
)

# Weekly: Multi-model cross-validation
scheduler.add_job(
    run_qc_cross_validation,
    trigger=CronTrigger(day_of_week="mon", hour=4, minute=0),
    kwargs={"scenarios": "all", "models": ["gpt-4o", "claude-sonnet", "gemini-pro"]},
    id="qc_weekly"
)

# On deploy: Immediate smoke test
async def on_deploy_qc():
    results = await run_qc_scenarios(count=5, strict=True)
    if any(r.score < 80 for r in results):
        await rollback()
        await alert("🚫 Deploy blocked: QC failed")
```

---

## QC Output Example

```
┌─────────────────────────────────────────────────┐
│  QC Report — Hourly #247                         │
│  Model: GPT-4o (test) → Coach → Claude (judge)  │
├─────────────────────────────────────────────────┤
│                                                  │
│  Scenarios: 3/3 passed                          │
│                                                  │
│  ✅ plan_no_injuries         Score: 94          │
│     Safety: 10/10  Accuracy: 9/10  Tone: 9/10  │
│                                                  │
│  ⚠️ fatigue_report           Score: 72          │
│     Relevance: 5/10 ← user said "tired from     │
│     work" but coach gave training advice        │
│     Fix: Added fatigue-management.md            │
│                                                  │
│  ✅ log_vague                Score: 88          │
│                                                  │
│  Next QC: 60 min (Claude Sonnet)                │
└─────────────────────────────────────────────────┘
```
