# ARCHITECTURE

Status: Current implementation view (reviewed 2026-03-02)

This document describes what is implemented now, and where target-state work remains.

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
	- `update_alankar_mastery(...)`
	- `update_phrase_mastery(...)`
	- compatibility path: `update_skill_progress(...)`

Current note:
- Forward-only unlock is implemented.
- Canonical unification to a single `skill_progress`-first path is still in progress.

## 5. Curriculum Engine
Skill Snapshot
 → Level Assignment
 → Content Unlock
 → Recommendation

Implemented in:
- `app/services/curriculum_service.py` (`evaluate_curriculum_progress`)
- `app/services/skill_profile.py` (`build_skill_profile`)

Current note:
- Recommendation now prioritizes newly unlocked content from newly mastered items.

## 6. Analytics Engine
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

## 7. Observability & Debug

Implemented:
- Debug endpoints in `app/routes/debug.py`
- Router mounted in `app/main.py`

Current note:
- Environment-gated debug enable/disable is planned, not yet enforced.

## 8. Validation Status

- Full test suite status: `23 passed` in conda environment `gokul`.
