"""
Seed the TEST knowledge base at tests/fixtures/knowledge_sample/
Minimal subset for unit tests. Must exist for Phase 2.

Run: python scripts/seed_test_kb.py
"""

from pathlib import Path

TEST_KB = Path(__file__).parent.parent / "tests" / "fixtures" / "knowledge_sample"

FILES = {
    "training-philosophy.md": "# Running Philosophy\n\n80/20 polarized training. 10% mileage rule. Consistency over intensity.",
    "admin-guidelines.md": "# Admin Guidelines\n\n1. KB-only. 2. Safety first. 3. No medical advice. 4. 80/20 enforcement.",
    "workouts/easy-run.md": "# Easy Run\n\nZone 2, conversational pace. 20-90 min. 3-5x/week.",
    "workouts/tempo-run.md": "# Tempo Run\n\nThreshold pace, comfortably hard. 20-40 min. 1x/week.",
    "programs/couch-to-5k.md": "# Couch to 5K\n\n8-12 weeks. 3 days/week. Walk-run intervals building to continuous 5K.",
    "programs/5k-improver.md": "# 5K Improver\n\n4 days/week. 6-week cycle with tempo, intervals, long run, taper.",
    "rules/pace-zones.md": "# Pace Zones\n\nZone 2: easy (60-70% HR). Zone 4: threshold (80-90%). Zone 5: VO2max (90-100%).",
    "rules/progression-rules.md": "# Progression\n\n10% weekly mileage increase max. 3 weeks build + 1 week down.",
    "rules/injury-guide.md": "# Injury Guide\n\nShin splints: reduce mileage, calf work. Runner's knee: strengthen hips. IT band: foam roll + glutes.",
}

for relpath, content in FILES.items():
    fp = TEST_KB / relpath
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)
    print(f"  ✅ {relpath}")

print(f"\n✅ Test KB seeded: {len(FILES)} files")
