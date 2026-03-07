# Current Sprint

## Focus
Post-V2 Execution (Slices 2-5 Completed)

## Remaining
- Run full `pytest` regression in configured environment (`pytest`/`conda` CLI unavailable in current shell).
- Tune learning model artifact with larger historical training window and compare MAE.
- Start next cycle scope for recommendation quality improvements and richer guidance UX.

## Experiments
- Offline recommendation model baselines from existing session/history data.
- Difficulty-estimation feature selection from current analytics/session indices.

## Sprint Note
- Architecture and phased plan docs are prepared and synced.
- Milestone V2.1 (Practice Studio visualization) is implemented and build-validated.
- Milestone V2.2 (Skill Radar chart) is implemented and build-validated.
- Milestone V2.3 (Practice History timeline) is implemented and build-validated.
- Milestone V2.4 (Technique Visualizer) is implemented and build-validated.
- Milestone V2.5 (Adaptive Coaching UI) is implemented and build-validated.
- Post-V2.5 adaptive coaching refinements are implemented and build-validated: immediate fallback from latest practice feedback and guarded auto-fetch of recommendation per new attempt.
- Adaptive Coach now uses deterministic coaching only in Practice Studio: LLM structured drill removed and replaced with payload-driven "Next Steps" guidance.
- Skill Radar and Practice History now auto-load on first page visit and continue to auto-refresh after new successful practice submissions.
- Dashboard and Progress now auto-load on first page visit, with manual refresh still available.
- Slice 1 completed: docs/architecture roadmap rebaselined for post-V2 execution.
- Locked next-phase decisions: new melody content type, ML-first recommendations, existing session/history training data, offline model artifact loading at backend startup, full-stack incremental delivery.
- Slice 2 in progress: added melody content-type plumbing end-to-end (songs catalog `content_type`, melody practice endpoint, practice response `content_type`, frontend melody practice mode + API submit path).
- Added initial famous/public-domain melody content pack: `melody_1`, `melody_2`, `melody_3`.
- Added melody catalog regression tests for unlock chain and content-type inference in `tests/test_song_catalog.py`.
- Slice 3 completed: melody progression/unlock hardening implemented (`infer_content_type` in curriculum rules, deterministic content list ordering).
- Slice 4 completed: ML-first learning engine added with offline-trainable artifact (`app/services/learning_engine.py`), startup loading, and analytics learning endpoints.
- Slice 5 completed: frontend learning-intelligence wiring added to Dashboard and Progress with difficulty/recommendation/model status surfaces.
- Validation status: backend compile (`python -m compileall`) and frontend build (`npm run build`) passing after each slice; slice regression checks executed via direct test-function invocation fallback.
