# Implementation Applied - Current Reality Check

Date: 2026-03-02

This document replaces older pre-hardening notes and reflects what is currently implemented in code.

## Applied Components

### 1) Database Foundation (`database/db.py`)

Implemented:
- `sessions` storage with composite and technique metrics.
- `analytics_snapshots` storage with rolling prune logic (max 30 per user).
- `alankar_mastery` and `phrase_mastery` tables with:
  - `successful_sessions` counter
  - forward-only unlock behavior
- `session_hash_registry` table with duplicate prevention in `save_session(...)`.
- `skill_progress` table scaffold exists.
- Legacy compatibility helpers restored for existing edge-case tests:
  - `update_skill_progress(...)`
  - session hash registry helpers
  - timezone and streak helpers
  - analytics pruning helper
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

- Timezone-aware streak subsystem is not implemented yet.
- Canonical progression architecture is still split between compatibility paths and newer flow.
- Debug endpoint enable/disable by environment is not yet in place.

## Validation Result

- Full test suite run completed in conda env `gokul`.
- Result: `23 passed`.

## Next Execution Plan

1. Add first-class streak domain model and timezone-safe progression APIs.
2. Consolidate unlock source-of-truth around `skill_progress` (reduce compatibility branching).
3. Add env-gated debug routing and production defaults.
4. Keep CI/local test parity with conda environment lock-step.
