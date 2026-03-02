# SYSTEM CORE

Status: Current implementation baseline (reviewed 2026-03-02)

## Purpose
AI-powered Hindustani flute tutor focused on structured mastery progression.

## Pedagogical Model
- Skill-first progression
- Technique-aware scoring
- Rhythm prioritized over speed
- Composite mastery required for unlock

## Evaluation Doctrine
- DTW alignment mandatory
- Pitch + timing weighted scoring
- Technique scoring affects composite
- No single-session unlock

Current implementation note:
- Technique detection and comparison run through `audio/techniques.py`.

## Unlock Policy
- 3 successful sessions above threshold
- No relocking once unlocked
- Progression is forward-only

Current implementation note:
- Enforced in canonical `update_skill_progress(...)` for all skill types.
- Forward-only unlock integrity is additionally guarded by DB check constraints.

## Analytics Philosophy
- Rolling window aggregation
- Weighted recent performance
- No metric inflation

Current implementation note:
- Rolling prune is active in `save_analytics_snapshot(...)`.
- Composite weighting is configurable in `app/services/analytics_config.py`.

## Curriculum Principles
- Skill snapshot drives progression decision.
- Unlocked but unmastered content is recommended next.
- Newly unlocked content gets recommendation priority.

## Streak Domain
- Timezone offset is user-level (`user_profile`).
- Logical day is computed from UTC timestamp + user offset.
- Idempotent per day using `practice_days` dedupe.
- Streak increments only on new logical-day records.

## Operational Reality
- Debug routes are environment-gated via `DEBUG_ENDPOINTS`.
- Production default keeps debug routes disabled.
- Timezone-safe streak is implemented in the DB layer.

## Validation Snapshot
- Latest targeted regression run: `16 passed` (`test_edge_cases.py`, `test_curriculum.py`).

## v1 Backend Freeze
Date: 2026-03-02
All freeze checklist items completed.
