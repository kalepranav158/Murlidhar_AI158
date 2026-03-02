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
- Enforced in `update_alankar_mastery(...)` and `update_phrase_mastery(...)`.
- Legacy compatibility helper `update_skill_progress(...)` is available for edge-case test coverage.

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

## Operational Reality
- Debug routes are currently mounted by default.
- Environment-gated debug switch is a planned hardening step.
- Timezone-safe streak is partially covered through compatibility paths and remains a target for first-class domain implementation.

## Validation Snapshot
- Latest full test run in conda env `gokul`: `23 passed`.
