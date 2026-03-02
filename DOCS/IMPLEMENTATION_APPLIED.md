# Implementation Applied - Current Reality Check

Date: 2026-03-02

This document replaces older pre-hardening notes and reflects what is currently implemented in code.

## Applied Components

### 1) Database Foundation (`database/db.py`)

Implemented:
- `sessions` storage with composite and technique metrics.
- `analytics_snapshots` storage with rolling prune logic (max 30 per user).
- `session_hash_registry` table with duplicate prevention in `save_session(...)`.
- canonical `skill_progress` model with:
  - `skill_type`-aware progression
  - `successful_sessions` and `total_sessions`
  - `composite_average` and `recent_weighted_average`
  - `last_composite_score`, `last_session_at`, unlock timestamps
  - DB-level unlock consistency checks
- streak domain implemented:
  - `user_profile` (timezone offset)
  - `practice_streak` (current/longest/total/logical date)
  - `practice_days` (idempotent daily dedupe)
- Session hash calculation in `save_session(...)` updated to include result payload fields to avoid false duplicate collapse across distinct attempts.

### 2) Analytics Configuration (`app/services/analytics_config.py`)

Implemented:
- Configurable `COMPOSITE_CONFIG` weights.
- Validation utility for config sanity.
- Rolling window analytics helpers:
  - weighted average
  - exponential weighted average
  - trend slope
  - consistency index

### 3) Debug Observability (`app/routes/debug.py`)

Implemented endpoints:
- `GET /debug/sessions/{user_id}`
- `GET /debug/alankar/{user_id}/{alankar_id}`
- `GET /debug/phrase/{user_id}/{song_id}/{phrase_id}`
- `GET /debug/analytics/{user_id}`
- `GET /debug/student/{user_id}`

### 4) App Integration (`app/main.py`)

Implemented:
- startup DB initialization (`init_db()`)
- debug router mounted by default

### 5) Curriculum + Technique Stabilization

Implemented:
- Curriculum recommendation now prioritizes content just unlocked by newly mastered items.
- Technique detection thresholds tuned for micro-jitter glide robustness.
- Interactive pitch detector script no longer blocks pytest collection.

## Open Gaps

- Debug endpoint enable/disable by environment is not yet in place.
- Optional retirement of legacy physical tables (`alankar_mastery`, `phrase_mastery`) after migration grace period.

## Validation Result

- Targeted canonical regression run completed.
- Result: `16 passed` (`test_edge_cases.py`, `test_curriculum.py`).

## Next Execution Plan

1. Add env-gated debug routing and production defaults.
2. Decide retention/decommission plan for old mastery tables.
3. Expand integration tests for route-level progression behavior.
4. Keep CI/local test parity with conda environment lock-step.
