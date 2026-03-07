# CHANGELOG

## [Unreleased]
- Updated Practice Studio form control typography so selection textboxes/dropdowns (and dropdown option text) use the Sanskrit-style font treatment
- Switched Documentation typography to a Sanskrit-style serif treatment (`Tiro Devanagari Sanskrit`) for section text and illustration headline labels
- Updated Documentation page typography: refreshed section text/captions styling and changed embedded SVG headline fonts for the flute and Govardhan illustrations
- Added relevant illustrations to the Documentation page sections (`Flute History` and `Lifting Govardhan Hill`) using local responsive SVG assets with captions
- Added final `Documentation` page tab with two cultural sections: a short flute history intro and a Shri Krishna stories section seeded with one short story (`Lifting Govardhan Hill`)
- Reworked Practice Studio selection controls into a responsive column/grid layout (with compact spacing) to reduce vertical form height and adapt better across screen sizes
- Expanded Curriculum Snapshot layout to use full available row width in Practice Studio and tuned responsive grid breakpoints to favor width over vertical stacking
- Replaced raw Curriculum Snapshot JSON in Practice Studio with a structured UI card showing level, score, recommendation, next goal, and unlocked/mastered/locked content pills
- Synced live-record 4-beat count-in with alankar metronome flow so recording begins exactly on a fresh `Sam` (cycle reset), with count-in running as a dedicated pre-roll phase
- Added `Clear Recording` action in Practice Studio live-record mode to discard recorded audio and preview before submitting
- Added a 4-beat pre-recording count-in in Practice Studio and upgraded metronome accents with tala cues (`Sam` strong, `Khali` lighter) plus live marker/status UI
- Tightened Practice Studio metronome sync with a clock-based timing loop aligned to alankar reference steps, and added a mini alankar metronome strip showing live `Now`/`Next` note cues
- Elevated the `Vrindavan Evening` theme with premium visual polish: luxe gradient title treatment, decorative atmospheric overlay, shimmering card surfaces, richer nav accents, and improved hover/focus motion for a more attractive frontend
- Activated theme variant `Vrindavan Evening` (option 2): deeper Krishna indigo shell, peacock teal accents, and feather-gold heading glow across the shared frontend palette
- Applied a Krishna-inspired frontend theme using peacock-feather colors (indigo, teal, jade, gold) across navigation, cards, controls, and interactive panels
- Added atmospheric multi-layer gradient/pattern background, upgraded typography, and consistent visual harmonization for Practice, Ask, Analytics, Skill Radar, and History surfaces
- Upgraded Practice Studio reference-note UX with a tempo-synced step guide: removed raw timestamp display and now shows beat-based step timing that updates with selected BPM
- Added an interactive metronome panel in Practice Studio for alankar/phrase rehearsal, including pulse visualization, cycle progress, mute toggle, and active-step highlighting
- Implemented Ask Guru structured response UI (mode badge, confidence, and readable field cards) instead of raw JSON-only rendering
- Added pre-practice selected phrase reference-note panel in Practice Studio for both upload and live recording workflows
- Added songs phrase-reference API endpoint `GET /songs/{song_id}/phrase/{phrase_index}` to power on-screen reference notes before submission
- Refactored analytics chart option builders into `frontend/src/modules/analytics/options/buildAnalyticsOptions.ts` and removed diagnostics-prefixed option naming from `Analytics` page wiring
- Enhanced Practice Studio heatmap with `Absolute Cents` / `Signed Cents` scale toggle for deviation analysis
- Added heatmap-to-timeline interaction: clicking a heatmap cell now highlights the corresponding time window on the pitch timeline
- Renamed top navigation label from `Diagnostics` to `Debug` while preserving the existing internal diagnostics route key
- Started next Practice Studio analytics slice: added a pitch-deviation heatmap panel (time-bin vs note with absolute cents intensity)
- Simplified `Diagnostics` into a debug-only surface by removing duplicated analytics chart blocks now hosted in the new `Analytics` page
- Added new top-level `Analytics` page and navigation tab; moved trend/error/instability chart experience into a dedicated analytics surface with first-visit auto-load
- Added explicit instability threshold visualization in Diagnostics: Stable/Watch/Critical background bands with dashed threshold ceiling lines
- Extended diagnostics charting: charts now auto-load on first page visit and include a new Instability Score panel (weighted from inverse accuracy, pitch error, and timing error)
- Implemented next internal diagnostics slice: added live ECharts panels for Accuracy Trend, Pitch Error Trend, and Timing Error Trend using `/analytics/trend` + `/sessions` data
- Fixed Skill Radar chart footprint: expanded ECharts container sizing and radar option layout so Skill Balance no longer renders as a narrow, clipped chart
- Added manual Rollup chunking in Vite config for `echarts`, `echarts-for-react`, and React vendor modules to improve deferred bundle composition
- Pruned unused ECharts registrations (`BarChart`, `HeatmapChart`, `VisualMap`, `Dataset`, `Title`) to reduce current chart payload until those chart types are introduced
- Switched Diagnostics smoke chart renderer to canvas and removed `SVGRenderer` registration for additional chart bundle reduction
- Started V3 Phase 3 progress analytics implementation: Progress page now renders ECharts-based Skill Improvement and Accuracy vs Composite trend charts sourced from session/history data
- Added route-level lazy loading for chart-heavy pages (`Progress`, `Skill Radar`, `Diagnostics`) to reduce initial app bundle size and defer ECharts chunk loading
- Completed V3 Phase 2 frontend visualization migration: Skill Radar renderer moved from custom SVG to ECharts with preserved normalized data mapping and source metadata cards
- Started V3 Phase 1 frontend visualization implementation: installed `echarts` + `echarts-for-react`, added shared chart infrastructure under `frontend/src/modules/charts`, added reusable chart container styles, and validated with successful frontend build
- Synced DOCS to V3 visualization execution blueprint: finalized Apache ECharts + `echarts-for-react` as chart stack with Phase 1 (foundation) and Phase 2 (Skill Radar migration) planning
- Synced frontend architecture/plan docs to include `Ask Guru` as a dedicated learner surface and keep Diagnostics internal
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
