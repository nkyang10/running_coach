"""
Seed the knowledge base with running training content.
Run once during setup: python scripts/seed_knowledge.py
"""

from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

FILES = {
    # ───────── CORE PHILOSOPHY ─────────
    "training-philosophy.md": """# Running Training Philosophy

## Core Principles

1. **Consistency Over Intensity** — Run often, mostly easy. 80% of weekly mileage at conversational pace.
2. **Progressive Overload** — Increase weekly mileage by max 10% per week. No jumps.
3. **Polarized Training** — 80% easy (Zone 2), 20% hard (intervals/tempo). The 80/20 rule.
4. **Listen to Your Body** — Niggles are warnings. Pain is a stop sign. Rest early, not late.
5. **Train the Person, Not the Pace** — Life stress, sleep, recovery all factor into training load.

## Coaching Style

- Data-driven but human-first. Numbers inform, don't dictate.
- Ask questions before prescribing. "How did that feel?" matters more than pace.
- Celebrate consistency. The runner who runs 4×/week for a year beats the one who runs 6×/week for a month.
- Recovery IS training. Sleep, nutrition, and rest days are part of the plan.
- Cross-training is not optional — core work, strength training, and mobility prevent injuries.
""",

    "admin-guidelines.md": """# Admin Guidelines for AI Behavior

## Rules for the AI Running Coach

1. **Knowledge Base Only** — DO NOT use running advice from outside this knowledge base.
   If you don't have information about a specific topic, say so honestly.

2. **Safety First** — If a runner reports pain (not soreness), ALWAYS take it seriously.
   • Sharp/stabbing pain → stop running, recommend medical evaluation
   • Dull ache → reduce load, suggest cross-training, monitor
   • Shin splints → reduce mileage, add calf strengthening
   • IT band → foam rolling, glute work, reduce downhill running

3. **No Medical Diagnosis** — You are a coach, not a doctor or physio.

4. **80/20 Enforcement** — Always check that weekly intensity balance follows 80/20.
   If a runner is doing too much hard running, flag it.

5. **10% Rule** — Flag any weekly mileage increase > 10%.

6. **Scale to Runner Level**
   - New runner (< 6 months): focus on consistency, walk-run is OK, no speed work yet
   - Intermediate (6mo-2yr): introduce tempo, strides, structured plans
   - Advanced (2yr+): full periodization, race-specific blocks

7. **Conflict Resolution** — If knowledge sources contradict, follow this priority:
   1. training-philosophy.md (overall methodology)
   2. rules/ (specific training rules)
   3. programs/ (race plans)
   4. workouts/ (individual session types)
""",

    # ───────── WORKOUT TYPES ─────────
    "workouts/easy-run.md": """# Easy Run (Zone 2)

## Purpose
Build aerobic base, improve fat metabolism, active recovery.
This is the foundation — 80% of all running.

## How
- **Pace**: Conversational. You can speak in full sentences.
- **Heart Rate**: Zone 2 (60-70% of max HR). Roughly: 180 minus your age.
- **Duration**: 20-90 minutes depending on level
- **Frequency**: 3-5× per week for most runners

## Why It Works
- Builds capillary density in muscles
- Strengthens tendons and ligaments with low injury risk
- Improves the body's ability to use fat as fuel
- Allows hard sessions to be truly hard (because easy days are truly easy)

## Common Mistakes
- Running easy runs too fast ("junk miles" in Zone 3)
- Skipping easy runs because they feel "too easy"
- Not enough volume — 20 minutes is fine for beginners

## Progression
- Beginner: Start with 15-20 min walk-run
- Add 5 min per week until reaching 45-60 min continuous
- Intermediate: 45-75 min
- Advanced: 60-90 min
""",

    "workouts/tempo-run.md": """# Tempo Run (Threshold)

## Purpose
Improve lactate threshold — the pace you can sustain for about 1 hour.
This is "comfortably hard" running.

## How
- **Pace**: 10K race pace + 10-15 sec/km, or 80-88% of max HR
- **Feel**: "Comfortably hard" — can say a few words, not full sentences
- **Duration**: 20-40 minutes of tempo effort (not including warm-up/cool-down)

## Types
- **Classic Tempo**: 20-30 min continuous at threshold pace
- **Cruise Intervals**: 3-5 × 5-8 min at threshold, 60-90s jog recovery
- **Progression Run**: Start easy, finish at threshold

## Frequency
- 1× per week for most runners
- Not for beginners (< 3 months consistent running)

## Warm-up / Cool-down
- 10-15 min easy jog warm-up
- 10 min easy jog cool-down
- Dynamic stretches before, static after
""",

    "workouts/interval-training.md": """# Interval Training (VO2max)

## Purpose
Improve VO2max and running economy. These are the HARD days.

## How
- **Pace**: 3K-5K race pace (very fast)
- **Effort**: 90-95% of max HR. You're counting seconds until it's over.
- **Work:Rest Ratio**: 1:1 or 1:0.5 (equal rest or half rest)

## Types
- **400m repeats**: 8-12 × 400m at 5K pace, 200m jog recovery
- **800m repeats**: 5-6 × 800m at 5K pace, 400m jog recovery
- **1K repeats**: 4-5 × 1K at 5K pace, 400m jog recovery
- **Pyramid**: 200-400-600-800-600-400-200 with equal jog rest

## Frequency
- 1× per week max
- Only after 3+ months of consistent base building
- NOT for beginners

## Warm-up / Cool-down
- 15-20 min easy jog warm-up with strides
- 10-15 min easy jog cool-down

## Safety
- Never do intervals two days in a row
- Skip if fatigued, sore, or sleep-deprived
- Track surface preferred over concrete
""",

    "workouts/long-run.md": """# Long Run

## Purpose
Build endurance, mental toughness, and time on feet.
The cornerstone of distance running.

## How
- **Pace**: Easy (Zone 2), or with fast-finish (last 20% at marathon pace)
- **Distance**: 20-30% of weekly mileage
- **Frequency**: 1× per week

## Progression
- Beginner: Add 1-1.5 km per week
- Max long run before race depends on goal:
  - 5K: 10-12 km
  - 10K: 14-16 km
  - Half marathon: 18-22 km
  - Marathon: 30-35 km

## Nutrition
- > 60 min: Consider fuel (gels, sports drink)
- > 90 min: Fuel is essential. 30-60g carbs per hour
- Hydrate throughout

## Recovery
- Long run day is NOT followed by a hard day
- Eat within 30 min of finishing (carbs + protein)
- Extra sleep the night before and after
""",

    "workouts/recovery-run.md": """# Recovery Run

## Purpose
Active recovery — flush out waste products, promote blood flow.
NOT a training stimulus. This is maintenance, not improvement.

## How
- **Pace**: Very easy. Slower than your easy run pace.
- **Heart Rate**: Zone 1 (< 60% max HR)
- **Duration**: 20-40 min max
- **When**: Day after a hard session or long run

## Rules
- If you feel tired BEFORE starting, skip it. Walk instead.
- Never extend a recovery run "because you feel good"
- Recovery runs don't build fitness — they help you absorb training

## Alternative
- 30-45 min walk is equally effective
- Light cycling or swimming works too
""",

    "workouts/strides.md": """# Strides

## Purpose
Improve running form, leg turnover, and neuromuscular efficiency.
Not a workout — a drill appended to easy runs.

## How
- **Distance**: 80-100m (roughly 20-25 seconds)
- **Pace**: Fast but relaxed — ~90% of max speed, NOT sprinting
- **Recovery**: Walk back or 60-90s easy jog between each
- **Volume**: 4-8 strides

## When
- After an easy run, 1-2× per week
- On grass or track — soft surface is better

## Form Focus
- Stay tall, don't lean forward
- Quick, light feet
- Relaxed shoulders and hands
- Land under your hips, not ahead of them

## Progression
- Start with 4 strides, add 1 per week until 8
- Beginner: wait 2 months before adding strides
""",

    "workouts/hill-repeats.md": """# Hill Repeats

## Purpose
Build leg strength, power, and running economy.
"Hills are speed work in disguise."

## How
- **Hill**: 6-8% grade, 100-200m long
- **Effort**: Hard but controlled (85-90% effort)
- **Recovery**: Jog down slowly (this IS the recovery)
- **Volume**: 6-10 repeats

## Form
- Shorten stride, increase cadence
- Drive arms, not legs
- Look ahead (10m), not at your feet
- Maintain effort, not pace (pace slows on hills — that's fine)

## Frequency
- 1× per week, replacing intervals
- Particularly useful in base-building phase

## Safety
- Avoid steep downhills for recovery jogging (stresses knees)
- If the hill flattens at the top, stop there
""",

    # ───────── CROSS-TRAINING ─────────
    "cross-training/strength-for-runners.md": """# Strength Training for Runners

## Purpose
Injury prevention, running economy, power.
Stronger runners are faster runners.

## Core Exercises (2× per week)

### Lower Body
- **Bodyweight Squats**: 3×15. Focus on depth, not speed.
- **Lunges** (forward + reverse): 3×10/side. Keep torso upright.
- **Single-Leg Deadlift**: 3×8/side. Hamstrings + glutes + balance.
- **Calf Raises**: 3×20. Both straight-leg and bent-knee.
- **Glute Bridges**: 3×15. Single-leg when ready.

### Core
- **Plank**: 3×30-60s. Keep hips level.
- **Side Plank**: 3×20-30s per side.
- **Dead Bug**: 3×10/side. Anti-extension for running posture.
- **Bird Dog**: 3×8/side. Cross-body stability.

### Upper Body (for arm drive)
- **Push-ups**: 3×8-15
- **Rows** (band or dumbbell): 3×10
- **Shoulder Taps** (from plank): 3×10/side

## When
- After easy runs (same day) or on non-running days
- Never before a hard session
- Not on long run day

## Progression
- Bodyweight → Add resistance bands → Add dumbbells
- Always prioritize form over weight
""",

    "cross-training/mobility.md": """# Mobility for Runners

## Daily (5-10 min)
- **Leg Swings**: Forward/back × 15, side-to-side × 15 per leg
- **Hip Circles**: 10 each direction
- **Ankle Rotations**: 10 each direction per ankle
- **World's Greatest Stretch**: 5/side
- **Cat-Cow**: 10 reps

## Post-Run (while warm)
- **Standing Calf Stretch**: 30s × 2 per leg (straight + bent knee)
- **Hip Flexor Stretch**: 30s × 2 per side
- **Hamstring Stretch** (lying, with strap): 30s × 2 per leg
- **Figure-4 Stretch**: 30s × 2 per side (glutes/piriformis)
- **Child's Pose**: 60s

## Key Mobility Areas for Runners
1. Ankles (dorsiflexion) → affects stride length and knee load
2. Hips (extension + rotation) → affects power and IT band
3. Thoracic spine (rotation) → affects arm swing and breathing
""",

    "cross-training/injury-prevention.md": """# Injury Prevention Exercises

## The Big 4 (2-3× per week)

### 1. Eccentric Calf Raises (Achilles + shin splints)
- Stand on step edge, both feet up, ONE foot down (5 seconds)
- 3×10 per leg
- Builds tendon resilience

### 2. Clamshells + Side-Lying Leg Raises (IT band + hips)
- Clamshells: 3×15/side (with band when ready)
- Side-lying leg raises: 3×12/side

### 3. Single-Leg Balance (ankle stability)
- Stand on one leg, eyes open → closed → on cushion
- 30-60s, build to 2 min

### 4. Monster Walks (glute activation)
- Resistance band around ankles, small steps sideways
- 3×10 steps each direction

## Pre-Run Activation (2-3 min before every run)
- Leg swings × 10 each
- 5 bodyweight squats
- 5 lunges per side
- Marching high knees × 10

## When to See a Professional
- Pain that worsens during a run (not just soreness)
- Pain that persists > 2 weeks despite rest
- Sharp/stabbing sensation (not dull ache)
- Swelling, bruising, or instability
""",

    # ───────── PROGRAMS ─────────
    "programs/couch-to-5k.md": """# Couch to 5K (Beginner)

## Goal
Run 5K continuously in 8-12 weeks. Starting from zero.

## Schedule
3 days/week (e.g., Mon/Wed/Fri or Tue/Thu/Sat)

## Structure
Each session: 5 min brisk walk warm-up → run/walk intervals → 5 min walk cool-down

### Phase 1: Walk-Run (Weeks 1-4)
- Week 1: 8× (1 min run / 1.5 min walk) = 20 min
- Week 2: 6× (1.5 min run / 2 min walk) = 21 min
- Week 3: 5× (2 min run / 1.5 min walk) = 17.5 min
- Week 4: 4× (3 min run / 1.5 min walk) = 18 min

### Phase 2: Build (Weeks 5-8)
- Week 5: 3× (5 min run / 2 min walk) = 21 min
- Week 6: 2× (8 min run / 2 min walk) = 20 min
- Week 7: 1× (20 min run) — first continuous run!
- Week 8: 25 min continuous run

### Phase 3: Consolidate (Weeks 9-12)
- Week 9: 28 min continuous
- Week 10: 30 min continuous
- Week 11: 32 min continuous (≈ 5K for most)
- Week 12: 5K attempt! Don't race — just finish.

## Weekly Pattern
Mon: Run | Wed: Run | Fri: Run | Rest all other days

## Cross-Training
- Add 2× core routine (15 min) after any run from Week 4
- Walk 30 min on non-running days from Week 6

## Milestones
- First continuous 5 min run
- First continuous 20 min run
- First 5K finish
""",

    "programs/5k-improver.md": """# 5K Improver (Intermediate)

## Goal
Improve 5K time. Already running 3-4×/week, 15-25 km/week.

## Schedule
4 days/week + 1 cross-training

## Weekly Pattern
- Mon: Easy run (30-45 min)
- Tue: Speed work (intervals or tempo)
- Wed: Rest or cross-train
- Thu: Easy run (30-45 min)
- Fri: Rest
- Sat: Long run (8-12 km easy)
- Sun: Rest

## 6-Week Cycle

### Week 1-2: Base
- Speed: 4× 400m at 5K goal pace, 200m jog
- Long run: 8-10 km easy
- Weekly mileage: ~20 km

### Week 3-4: Build
- Speed: 6× 400m at 5K goal pace, 200m jog OR 20 min tempo
- Long run: 10-12 km easy
- Weekly mileage: ~25 km

### Week 5: Peak
- Speed: 5× 600m at goal pace, 300m jog
- Long run: 10 km easy with last 2 km at race pace
- Weekly mileage: ~25 km

### Week 6: Taper
- Mon: Easy 20 min + 4 strides
- Tue: 3× 400m at race pace (very light)
- Thu: Easy 15 min
- Sat/Sun: RACE DAY 🏁

## Pace Zones (based on 5K race pace)
- Easy: Race pace + 60-90 sec/km
- Tempo: Race pace + 15-20 sec/km
- Intervals: Race pace
""",

    "programs/half-marathon.md": """# Half Marathon Plan (12 Weeks)

## Prerequisites
- Running 3-4×/week for 6+ months
- Comfortable with 10K distance
- Weekly mileage: 25+ km before starting

## Schedule
4 days/week + 1 cross-training

## Weekly Pattern
- Mon: Rest
- Tue: Speed/Tempo
- Wed: Easy run (6-10 km)
- Thu: Rest or cross-train
- Fri: Easy run (5-8 km)
- Sat: Long run (builds from 10K to 18-20K)
- Sun: Recovery or rest

## 12-Week Build

### Phase 1: Base (Weeks 1-4)
- Long runs: 10K → 12K → 14K → 12K (down week)
- Speed: Tempo 15-20 min
- Weekly: 25-30 km

### Phase 2: Build (Weeks 5-8)
- Long runs: 14K → 16K → 18K → 14K (down week)
- Speed: Tempo 25-30 min OR intervals 4-5× 1K
- Weekly: 30-38 km

### Phase 3: Peak (Weeks 9-10)
- Long run: 20K (once), then 16K
- Speed: Race pace 3× 2K, 400m jog
- Weekly: 35-40 km

### Phase 4: Taper (Weeks 11-12)
- Week 11: 60% of peak volume. Long run 12-14K.
- Week 12 (race week): Very light. Short runs + strides. Rest 2 days before race.

## Key Sessions Explained
- **Race Pace Runs**: Run sections at goal HM pace to dial in feel
- **Long Run with Fast Finish**: Last 3-5 km at goal race pace
- **Tempo**: Builds lactate threshold — critical for half marathon

## Nutrition During Long Runs
- > 60 min: Start fueling. Gel every 30-40 min.
- Practice race-day nutrition on long runs
- Nothing new on race day
""",

    # ───────── RULES ─────────
    "rules/pace-zones.md": """# Pace & Heart Rate Zones

## RPE Scale (1-10)
| RPE | Effort | Can You... | When to Use |
|-----|--------|------------|-------------|
| 1-2 | Very easy | Sing | Recovery, warm-up |
| 3-4 | Easy | Full conversation | 80% of runs |
| 5-6 | Moderate | Short sentences | Tempo, long run |
| 7-8 | Hard | Few words | Intervals |
| 9-10 | Max | Nothing | Race finish, hill sprints |

## Heart Rate Zones (based on max HR)
| Zone | % Max HR | Purpose |
|------|----------|---------|
| Z1 | < 60% | Recovery |
| Z2 | 60-70% | Aerobic base (80% of mileage) |
| Z3 | 70-80% | "Junk miles" — avoid for easy runs |
| Z4 | 80-90% | Threshold / tempo |
| Z5 | 90-100% | VO2max / intervals |

## When to Use Pace vs HR
- **HR**: For easy runs — keeps you honest (don't creep into Zone 3)
- **Pace**: For workouts — HR lags behind effort
- **RPE**: Always. The best metric. "How did that feel?"

## Finding Your Max HR
- NOT 220-age (can be ±20 bpm off)
- Field test: Warm up 15 min → Run 3 min hard uphill → Jog 2 min → Run 3 min hard uphill → Note highest HR
- Or: Use a recent 5K race — peak HR in last km
""",

    "rules/progression-rules.md": """# Progression Rules for Running

## The 10% Rule
- Increase weekly mileage by **no more than 10%** per week.
- Example: 20 km → 22 km → 24.2 km → 26.6 km

## The 3-Week Rule
- Increase for 3 weeks, then take a down week (reduce 20-30%)
- Build → Build → Build → Down
- Prevents cumulative fatigue and overuse injuries

## Adding Speed Work
- Wait until 3+ months of consistent base running
- Add 1 speed session per week
- Reduce easy run mileage slightly when adding intensity

## Long Run Progression
- Increase by 1-2 km per week
- Long run should be 20-30% of weekly mileage (not more)
- Every 3-4 weeks, reduce long run by 25% (down week)

## When NOT to Progress
- Sleep quality declining
- Resting HR elevated > 5 bpm above baseline
- Persistent soreness (not just training soreness)
- Life stress is high (work, travel, family)
- Any new niggle or pain

## Stagnation ≠ Regression
- Holding the same mileage for a few weeks IS progress
- The body adapts during plateaus too
- Not every week needs to be bigger than the last
""",

    "rules/deload-taper.md": """# Deload & Taper Weeks

## Deload (Training Cycle Recovery)

### When
- Every 4th week (3 weeks build + 1 deload)
- When RPE is climbing but pace is stagnating
- Elevated resting HR for 3+ days
- Persistent fatigue or low motivation

### Structure
- Mileage: 60-70% of peak week
- Intensity: Same (keep the quality, reduce the quantity)
- Example: 40 km peak → 25-28 km deload
- All runs at easy pace (no speed work)

## Taper (Pre-Race)

### 5K Taper
- Race week: 50-60% of normal volume
- 2 days before: very light 20 min + 4 strides
- Day before: rest or 15 min easy

### 10K Taper
- 10-14 days: 70% → 60% → 50% volume
- Keep some race pace work (reduced volume)
- 2 days before: rest

### Half Marathon Taper
- 2 weeks: Week 1 at 60%, Week 2 at 40%
- Last long run: 14 days before race (12-14 km)
- Last speed work: 10 days before (light)
- Race week: easy runs only, rest 2 days before

### Marathon Taper
- 3 weeks: 70% → 50% → 30%
- Last long run: 3 weeks before (25-28 km)
- Last marathon pace work: 2 weeks before
- Race week: very easy 30-40 min runs

## Taper Mistakes
- Doing too much ("I feel fresh, let me run more") — TRUST the taper
- Doing too little (losing feel for pace)
- Trying to make up missed training during taper
- Eating differently than normal
""",

    "rules/injury-guide.md": """# Running Injury Guide

## Warning Signs
- **Pain during a run that gets WORSE as you continue** → Stop. Walk home.
- **Pain that alters your gait** (limping, favoring one side) → Stop.
- **Sharp/stabbing sensation** → Stop. This is not training pain.
- **Dull ache that stays the same or improves** → Monitor. OK to continue.

## Common Running Injuries

### Shin Splints
- **What**: Pain along inner shin bone (tibia)
- **Cause**: Too much, too soon. Hard surfaces. Old shoes.
- **Fix**: Reduce mileage 50%. Ice after runs. Calf stretches + eccentric calf raises.
- **Cross-train**: Pool running, cycling — anything non-impact
- **Return**: Gradually over 2-3 weeks. Softer surfaces.

### Runner's Knee (PFPS)
- **What**: Pain around/behind kneecap
- **Cause**: Weak hips/glutes, sudden mileage jump, downhill running
- **Fix**: Strengthen hips (clamshells, side leg raises). Reduce downhill.
- **Taping**: Can help short-term. Doesn't fix the root cause.
- **Return**: When pain-free for 5+ days. Start with flat routes.

### IT Band Syndrome
- **What**: Pain on outside of knee, typically starts at same point in run
- **Cause**: Weak glute medius, tight IT band/TFL, cambered roads, worn shoes
- **Fix**: Foam rolling (IT band + TFL). Glute strengthening. Stop downhill running temporarily.
- **Cross-train**: Swimming, cycling (if pain-free)
- **Return**: When pain-free on flat ground. Strengthen aggressively.

### Plantar Fasciitis
- **What**: Heel/arch pain, worst in the morning or after sitting
- **Cause**: Tight calves, sudden mileage increase, unsupportive shoes
- **Fix**: Calf stretching (straight + bent knee, 3×/day). Roll arch with frozen water bottle.
- **Night splint**: Worth trying. Keeps fascia stretched overnight.
- **Return**: When morning pain-free for 5+ days. Build mileage slowly.

### Achilles Tendinopathy
- **What**: Pain/stiffness in Achilles tendon (above heel)
- **Cause**: Sudden hill work, speed work, or mileage increase. Tight calves.
- **Fix**: Eccentric heel drops (key rehab exercise). Reduce speed work. Avoid hills.
- **Important**: This responds to LOAD, not complete rest. Tendons need controlled stress to heal.
- **Return**: Gradual, over 4-6 weeks minimum.

## When to See a Professional
- Pain lasting > 2 weeks despite rest and rehab
- Pain that worsens despite reducing training
- Swelling, bruising, or visible deformity
- Any numbness or tingling

## The Comeback Rule
After any injury break > 2 weeks: start at 50% of pre-injury mileage.
Build back over the same number of weeks you were off.
""",

    "rules/shoe-guide.md": """# Running Shoe Guide

## When to Replace
- **400-600 km** is the typical lifespan
- Midsole foam compresses over time — you may not see it, but your legs will feel it
- Signs: new aches in shins/knees, shoes feel "dead," tread wear

## Rotation
- Having 2 pairs in rotation extends the life of both
- Alternate: one for easy runs, one for speed work
- Let each pair rest 24 hours between runs (foam decompresses)

## Types
- **Daily Trainer**: Cushioned, durable. For most easy + long runs.
- **Speed/Tempo Shoe**: Lighter, responsive. For intervals and tempo runs.
- **Race Shoe**: Lightweight performance. Carbon plate optional. Race day only.
- **Trail Shoe**: Grip + protection. For off-road running.

## Tracking
- Record shoe mileage in your profile: /shoes add "Nike Pegasus"
- Coach auto-tracks and warns you at 400 km
- Builds shoe rotation recommendations based on mileage
""",
}


def seed():
    print(f"Seeding running knowledge base at: {KNOWLEDGE_DIR}")
    for filepath, content in FILES.items():
        full_path = KNOWLEDGE_DIR / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content.strip())
        print(f"  ✅ {filepath}")

    (KNOWLEDGE_DIR / "README.md").write_text("""# Running Knowledge Base

Curated training knowledge for the AI Running Coach.

## Structure
- `training-philosophy.md` — Core coaching methodology (80/20, progression)
- `admin-guidelines.md` — AI behavior rules
- `workouts/` — Run types: easy, tempo, intervals, long run, recovery, strides, hills
- `cross-training/` — Strength, mobility, injury prevention for runners
- `programs/` — Training plans: Couch to 5K, 5K improver, Half Marathon
- `rules/` — Pace zones, progression, deload/taper, injury guide, shoes

## Editing
Edit files to customize. After editing: `/admin_reload` in the bot.
All changes tracked in git.
""")
    print(f"  ✅ README.md")
    print(f"\nDone: {len(FILES)} knowledge files seeded")


if __name__ == "__main__":
    seed()
