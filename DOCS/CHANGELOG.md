# CHANGELOG

## [Unreleased]
- Completed Slice 5 frontend learning-intelligence wiring: Dashboard/Progress now render ML learning difficulty and recommendation guidance with model-status visibility
- Completed Slice 4 ML-first learning engine: added `app/services/learning_engine.py`, offline artifact bootstrap (`app/config/learning_model_artifact.json`), startup model loading, and offline trainer script (`scripts/train_learning_model.py`)
- Added learning analytics endpoints: `/analytics/learning/skill-profile`, `/analytics/learning/difficulty`, `/analytics/learning/recommendation`, `/analytics/learning/model-status`, `/analytics/learning/model-refresh`
- Added learning-engine regression coverage in `tests/test_learning_engine.py`
- Completed Slice 3 melody progression integration: curriculum now uses canonical `infer_content_type` and deterministic sorted unlock/mastered content ordering
- Added melody progression regression coverage in `tests/test_melody_progression_rules.py`
- Added melody catalog regression coverage in `tests/test_song_catalog.py` for unlock-chain integrity and `infer_content_type` inference.
- Added famous/public-domain melody pack files: `melody_1` (Twinkle Twinkle), `melody_2` (Ode to Joy), `melody_3` (Happy Birthday)
- Started Slice 2 melody foundation: added songs catalog `content_type` support (response + optional filter query)
- Added melody practice backend route and service wiring (`/practice/melody/{user_id}/{melody_id}/{phrase_index}`) with content-type validation
- Extended practice response schema/normalization with `content_type` and frontend normalized `contentType`
- Added frontend melody submission path: API client + `usePracticeSession` hook + Practice page `Melody Practice` mode
- Added backend melody progression helper integration in curriculum/mastery checks (`is_melody_mastered`)
- Rebaselined post-V2 roadmap docs for slice-based execution and locked implementation decisions
- Updated V2 planning/architecture docs with approved next track: new melody content type + ML-first learning engine (offline model loading)
- Added first-visit auto-load for Dashboard and Progress pages to reduce manual fetch steps
- Added first-visit auto-load for Skill Radar and Practice History pages, while preserving submit-triggered refresh behavior
- Removed Adaptive Coach LLM structured-drill flow and `/ask` dependency from Practice Studio
- Added deterministic Adaptive Coach "Next Steps" guidance generated from practice payload + analytics recommendation
- Added post-V2.5 adaptive coaching UX hardening: immediate coach-plan fallback from practice `raw_feedback` plus per-attempt auto-fetch of adaptive recommendation
- Updated Adaptive Coaching UI copy/actions to reflect proactive recommendation loading (`Refresh Adaptive Recommendation`) and improved empty-state messaging
- Completed V2 Milestone V2.5 (Adaptive Coaching UI) inside Practice Studio with actionable drill cards and optional coaching fetch actions
- Added adaptive-coach module with drill-card mapping from `adaptive_plan` + `song_adaptive_plan` and integration for `/analytics/recommendation-adaptive_plan`
- Extended normalized practice result with adaptive drill fields (`targetDrill`, `exerciseMode`, `variationStrategy`, `tempoFeedback`, `songRecommendation`)
- Completed V2 Milestone V2.4 (Technique Visualizer) inside Practice Studio with expected-vs-observed transition overlays
- Added technique-visualizer module with transition mapping from `technique_details.expected_transitions` and `technique_details.found_transitions`
- Added visual scoring surface for per-transition position/strength/clarity/composite feedback with fallback states when details are absent
- Completed V2 Milestone V2.3 (Practice History timeline) with dedicated page and navigation tab
- Added practice-history module (hook + timeline panel + timeline mapper) with deterministic event badges: improvement, plateau, unlock
- Added history normalization path (`normalizePracticeHistory`) to keep timeline data envelope-safe and UI-stable
- Completed V2 Milestone V2.2 (Skill Radar chart) with dedicated page and navigation tab
- Added skill-radar module (hook + SVG radar chart + panel) with 5-dimension mapping: Pitch, Rhythm, Technique, Consistency, Progress
- Added radar normalization fallback rules using sessions and analytics snapshots when radar payload omits technique/progress dimensions
- Started V2 frontend implementation with Milestone V2.1 (Practice Studio)
- Added practice-studio module with timeline visualization components (`PitchTimeline`, `ReferenceNoteBar`, `UserPitchCurve`, `TechniqueMarker`)
- Upgraded Practice page to render interactive Practice Studio instead of raw practice JSON output
- Added additive practice response field `reference_notes` for accurate reference melody lane rendering
- Added V2 frontend architecture design doc (`DOCS/FRONTEND_ARCHITECTURE_V2.md`)
- Added V2 phased implementation plan (`DOCS/FRONTEND_V2_IMPLEMENTATION_PLAN.md`)
- Synced architecture and sprint docs with V2 planning baseline
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
