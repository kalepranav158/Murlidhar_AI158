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

## 2) Update Mastery (Alankar)

```python
from database.db import update_alankar_mastery

update_alankar_mastery(
    user_id="user_123",
    alankar_id="alankar_1",
    level_index=1,
    tempo=70,
    threshold=0.75,
    analytics={
        "indices": {"composite_score": 0.82},
        "volatility": 4.0,
    },
)
```

Unlock behavior:
- increments `successful_sessions` only on success
- unlocks when successful sessions reach 3
- unlock is forward-only

## 3) Update Phrase Mastery (Song)

```python
from database.db import update_phrase_mastery

update_phrase_mastery(
    user_id="user_123",
    song_id="song_1",
    phrase_id=1,
    accuracy=92.0,
    pitch_error=9.5,
    timing_error=0.04,
    analytics={"volatility": 3.2},
)
```

## 4) Save Analytics Snapshot (Auto-Pruned)

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

## 5) Debug Endpoints

```bash
# Sessions
GET /debug/sessions/{user_id}?limit=10

# Alankar mastery row
GET /debug/alankar/{user_id}/{alankar_id}

# Phrase mastery row
GET /debug/phrase/{user_id}/{song_id}/{phrase_id}

# Analytics window
GET /debug/analytics/{user_id}?limit=30

# Student progress
GET /debug/student/{user_id}
```

## 6) Environment / Validation Commands

```bash
# Syntax health check
python -m compileall -q app database analytics dtw evaluation llm music audio

# Test run (requires pytest installed in active environment)
python -m pytest -q

# Conda (gokul) explicit test run
C:/Users/Pranav/miniconda3/Scripts/conda.exe run -n gokul --no-capture-output python -m pytest -q
```
