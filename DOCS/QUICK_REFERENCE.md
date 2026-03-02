# Quick Reference (Current Build)

Date: 2026-03-02

This reference is intentionally limited to functions and endpoints that are currently available.

## 1) Save a Practice Session (Duplicate-Safe)

```python
from database.db import save_session

result = save_session(
    user_id="user_123",
    reference=[{"note": "Sa", "start": 0.0, "end": 0.5}],
    played=[{"note": "Sa", "start": 0.02, "end": 0.52}],
    result={
        "note_accuracy": 88.0,
        "avg_pitch_error_cents": 12.0,
        "avg_timing_error_sec": 0.05,
        "mistakes": [],
        "composite_score": 0.81,
        "pitch_index": 0.86,
        "rhythm_index": 0.79,
        "consistency_index": 0.82,
        "technique_score": 0.75,
    },
)

# result: {"status": "saved"} or {"status": "duplicate_rejected"}
```

## 2) Update Canonical Skill Progress

```python
from database.db import update_skill_progress

update_skill_progress(
    user_id="user_123",
    skill_id="alankar_1",
    skill_type="alankar",
    composite_score=0.82,
    threshold=0.75,
    session_hash="optional_deterministic_hash",
)
```

Unlock behavior:
- increments `successful_sessions` only on success
- unlocks when successful sessions reach 3
- unlock is forward-only

## 3) Update Phrase Progress (Song)

```python
from database.db import update_skill_progress

update_skill_progress(
    user_id="user_123",
    skill_id="song_1:phrase:1",
    skill_type="phrase",
    composite_score=0.92,
    threshold=0.90,
    session_hash="optional_deterministic_hash",
)
```

## 4) Update Practice Streak (Timezone-Safe)

```python
from database.db import set_user_timezone, update_practice_streak

set_user_timezone("user_123", timezone_offset_minutes=330)
streak = update_practice_streak("user_123")
```

Streak behavior:
- uses `logical_date = utc_now + user_offset`
- dedupes by `(user_id, logical_date)` via `practice_days`
- same-day repeated submissions do not double increment

## 5) Save Analytics Snapshot (Auto-Pruned)

```python
from database.db import save_analytics_snapshot

save_analytics_snapshot(
    "user_123",
    {
        "average_accuracy": 84.5,
        "trend_slope": 1.2,
        "predicted_next_accuracy": 85.7,
        "consistency_index": 0.81,
        "difficulty_recommendation": "medium",
        "trend_label": "improving",
    },
)
```

Pruning behavior:
- Keeps only latest 30 snapshots per user.

## 6) Debug Endpoints

```bash
# Sessions
GET /debug/sessions/{user_id}?limit=10

# Alankar skill progress row
GET /debug/alankar/{user_id}/{alankar_id}

# Phrase skill progress row
GET /debug/phrase/{user_id}/{song_id}/{phrase_id}

# Analytics window
GET /debug/analytics/{user_id}?limit=30

# Student progress
GET /debug/student/{user_id}
```

## 7) Environment / Validation Commands

```bash
# One-command backend freeze audit
python freeze_audit.py

# Syntax health check
python -m compileall -q app database analytics dtw evaluation llm music audio

# Test run (requires pytest installed in active environment)
python -m pytest -q

# Conda explicit test run (workspace-configured env)
C:/Users/Pranav/miniconda3/Scripts/conda.exe run -p C:/Users/Pranav/miniconda3 --no-capture-output python -m pytest -q
```
