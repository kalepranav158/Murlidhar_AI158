# Current Sprint

## Focus
Frontend Architecture V2 (Implementation In Progress)

## Remaining
- V2 frontend milestone sequence complete; next sprint planning pending.

## Experiments
- Radar dimension balancing (technique/progress derivation from existing payloads)
- Overlay calibration for detected pitch vs reference notes

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
