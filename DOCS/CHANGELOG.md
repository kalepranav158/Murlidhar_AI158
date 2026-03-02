# CHANGELOG

## [Unreleased]
- Canonicalized progression to `skill_progress` single update path (`update_skill_progress`)
- Removed legacy progression wrappers (`update_alankar_mastery`, `update_phrase_mastery`)
- Wired `practice_service` directly to canonical progression with deterministic per-skill session hashes
- Implemented timezone-safe, idempotent streak domain using `practice_days` logical-date dedupe
- Updated debug endpoints to read canonical `skill_progress` records
- Gated debug router mounting with `DEBUG_ENDPOINTS` (`false` by default)
- Archived legacy mastery tables to `_legacy_alankar_mastery` and `_legacy_phrase_mastery` with read-only compatibility views
- Added backend freeze validation suite in `test_backend_freeze.py` (integration chain, duplicate stress, integrity, streak boundaries, analytics window, load simulation, constraints)
- Synced architecture and reference docs to new canonical model
- Updated docs/test references to current targeted canonical suite (`16 passed`)

## v1 Backend Freeze
Date: 2026-03-02
All freeze checklist items completed.

## 2026-03-02
- Replaced stale implementation claims with verified module-level status
- Updated quick reference to only include currently available APIs/helpers
- Added environment health note: `pytest` not installed in configured conda env
- Added phased roadmap for next implementation cycle

## v0.9
- Added mastery counter
- Added no-relock policy
- Introduced streak tracking

## v1.0
- Curriculum stabilized
- Analytics window standardized
