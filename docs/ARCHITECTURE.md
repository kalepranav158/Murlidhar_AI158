# ARCHITECTURE

Status: Current implementation view (post-restructure)

This document describes the current VENORA architecture and where each major capability is implemented.

## 1. Evaluation Pipeline

WAV Input
-> Pitch Extraction
-> Note Segmentation
-> DTW Alignment
-> Scoring

Implemented in:
- `backend/utils/audio/pitch_detector.py`
- `backend/utils/audio/note_segmenter.py`
- `backend/utils/dtw/aligner.py`
- `backend/utils/evaluation/scorer.py`

## 2. Technique Engine

Pitch contour
-> Meend/Gamak detection
-> Reference comparison
-> Technique score

Implemented in:
- `backend/utils/audio/techniques.py`

## 3. Practice and Adaptive Flow

Session metrics
-> Mistake analysis
-> Adaptive recommendation
-> Tempo guidance

Implemented in:
- `backend/services/practice_service.py`
- `backend/services/adaptive_engine.py`
- `backend/services/song_engine.py`

## 4. Progression and Mastery

Aggregated performance
-> Mastery tracking
-> Unlock decisions
-> Next content recommendation

Implemented in:
- `backend/models/db.py` (`update_skill_progress`, progression persistence)
- `backend/services/curriculum_service.py`
- `backend/services/skill_profile.py`

## 5. Streak Engine

UTC timestamp
-> Logical local day
-> Daily dedupe
-> Streak update

Implemented in:
- `backend/models/db.py`

Key functions:
- `set_user_timezone(...)`
- `get_logical_date(...)`
- `update_practice_streak(...)`

## 6. Analytics Engine

Session history
-> Rolling aggregation
-> Index normalization
-> Trend/radar outputs

Implemented in:
- `backend/api/analytics.py`
- `backend/services/analytics_engine.py`
- `backend/services/analytics_helpers/analytics_service.py`
- `backend/models/db.py` (`save_analytics_snapshot`, rolling prune)

## 7. API Layer

FastAPI entrypoint and routers:
- `backend/main.py`
- `backend/api/practice.py`
- `backend/api/songs.py`
- `backend/api/sessions.py`
- `backend/api/analytics.py`
- `backend/api/ask.py`
- `backend/api/student.py`
- `backend/api/debug.py` (enabled only when `DEBUG_ENDPOINTS=true`; default is `false`)

## 8. Data Layout

- `data/db/` -> SQLite files
- `data/songs/catalog/` -> alankar/melody/song JSON catalog
- `data/knowledge/app_knowledge/` -> RAG text corpus
- `data/vector_db/app_vector_db/` -> persisted vector store artifacts

## 9. Validation Status

Current verification in this refactor branch:
- `freeze_audit.py` passed
- `pytest tests -q` passed (`42 passed, 4 skipped`)
- `frontend` production build passed (`npm run build`)

## 10. Frontend Planning References

- `docs/FRONTEND_ARCHITECTURE_V2.md`
- `docs/FRONTEND_V2_IMPLEMENTATION_PLAN.md`
