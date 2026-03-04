# ARCHITECTURE

Status: Current implementation view (reviewed 2026-03-02)

This document describes the current implemented architecture.

## 1. Evaluation Pipeline
WAV
 → Pitch Extraction
 → Pitch Smoothing
 → Note Segmentation
 → DTW Alignment
 → Evaluation Scoring

Implemented in:
- `audio/pitch_detector.py`
- `audio/note_segmenter.py`
- `dtw/aligner.py`
- `evaluation/scorer.py`

## 2. Technique Engine
Pitch Contour
 → Meend Detection
 → Gamak Detection
 → Expected Transition Matching
 → Technique Composite Score

Implemented in:
- `audio/techniques.py` (`detect_techniques`, `compare_with_reference`)

Current note:
- Micro-jitter handling and monotonic meend detection thresholds are tuned for test stability.

## 3. Adaptive Engine
Session Metrics
 → Tempo Deviation
 → Weak Area Detection
 → Drill Recommendation
 → Tempo Adjustment

Implemented in:
- `app/services/adaptive_engine.py`
- `app/services/practice_service.py`

## 4. Mastery Engine
Aggregated Composite
 → Threshold Check
 → Mastery Counter
 → Unlock Trigger

Implemented in:
- `database/db.py`
	- `update_skill_progress(...)` (single canonical update path)

Current note:
- Forward-only unlock is implemented.
- `skill_progress` is now the source of truth for alankar and phrase unlock progression.

## 5. Streak Engine
UTC Timestamp
 → User Timezone Offset
 → Logical Date
 → Idempotent Daily Insert
 → Streak Update

Implemented in:
- `database/db.py`
	- `set_user_timezone(...)`
	- `get_logical_date(...)`
	- `update_practice_streak(...)`
	- `practice_days` table (daily dedupe)

## 6. Curriculum Engine
Skill Snapshot
 → Level Assignment
 → Content Unlock
 → Recommendation

Implemented in:
- `app/services/curriculum_service.py` (`evaluate_curriculum_progress`)
- `app/services/skill_profile.py` (`build_skill_profile`)

Current note:
- Recommendation now prioritizes newly unlocked content from newly mastered items.

## 7. Analytics Engine
Session History
 → Rolling Aggregation
 → Index Normalization
 → Snapshot Generation

Implemented in:
- `database/db.py` (`save_analytics_snapshot`, rolling prune)
- `app/services/analytics_config.py` (`RollingWindowAnalytics`, composite config)

Current note:
- Rolling window pruning is active.
- Configurable weights are active via `COMPOSITE_CONFIG`.

## 8. Observability & Debug

Implemented:
- Debug endpoints in `app/routes/debug.py`
- Router mounted conditionally in `app/main.py` (`DEBUG_ENDPOINTS=true` only)

Current note:
- Environment-gated debug enable/disable is enforced.

## 9. Validation Status

- Targeted canonical regression suite status: `16 passed` (`test_edge_cases.py`, `test_curriculum.py`).

## 10. Frontend V2 Architecture (Planned)

Current implementation note:
- Backend contracts already expose the required data for V2 frontend evolution (practice payload overlays, radar endpoint, sessions timeline source, adaptive recommendation payloads).
- V2 is planned as a frontend-first upgrade without backend progression-logic changes.

Planning references:
- `DOCS/FRONTEND_ARCHITECTURE_V2.md`
- `DOCS/FRONTEND_V2_IMPLEMENTATION_PLAN.md`

## v1 Backend Freeze
Date: 2026-03-02
All freeze checklist items completed.
