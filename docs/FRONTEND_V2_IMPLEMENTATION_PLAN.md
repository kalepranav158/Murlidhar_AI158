# Frontend V2 Implementation Plan (Synced)

Status: V2 implemented; post-V2 slices 1-5 completed; V3 visualization phases planned (2026-03-05)

This plan is sequenced to match the approved V2 rollout order and current backend contracts.

## 0) Implementation Status
- [x] Milestone V2.1 G현 Practice Studio visualization
- [x] Milestone V2.2 G현 Skill Radar chart
- [x] Milestone V2.3 G현 Practice History timeline
- [x] Milestone V2.4 G현 Technique Visualizer
- [x] Milestone V2.5 G현 Adaptive Coaching UI

## 0.1) Post-V2 Slice Status
- [x] Slice 1 G현 Documentation + architecture rebaseline
- [x] Slice 2 G현 Melody content type foundation
- [x] Slice 3 G현 Melody content expansion pack
- [x] Slice 4 G현 Learning engine upgrade (ML-first)
- [x] Slice 5 G현 Frontend learning-intelligence wiring

## 1) Execution Order (Approved)
1. Practice Studio visualization
2. Skill Radar chart
3. Practice History timeline
4. Technique Visualizer
5. Adaptive Coaching UI

## 2) Milestone Plan

### Milestone V2.1 G현 Practice Studio Visualization
Objective:
- Replace basic practice result card with interactive studio visualization.

Scope:
- Introduce module `src/modules/practice-studio`
- Implement components:
  - `PitchTimeline`
  - `ReferenceNoteBar`
  - `UserPitchCurve`
  - `TechniqueMarker`
- Wire to existing practice submission flow (`/practice/alankar`, `/practice/song`).

API dependencies:
- practice payload: `detected_notes`, `alignment_debug`, `techniques`, `technique_details`, `evaluation`.

Exit criteria:
- User sees reference + detected pitch timeline after each submission.
- Missing optional fields degrade gracefully (no crash).

---

### Milestone V2.2 G현 Skill Radar Chart
Objective:
- Add radar model view for core skill balance.

Scope:
- Introduce module `src/modules/skill-radar`
- Add dedicated Skill Radar page and nav entry.
- Define normalized radar model with 5 dimensions.

API dependencies:
- `GET /analytics/radar`
- `GET /sessions` (for temporary technique dimension derivation if needed)
- existing student analytics snapshot for progress dimension mapping.

Exit criteria:
- Radar displays Pitch/Rhythm/Consistency/Composite-derived dimensions.
- Error/no-data states handled via existing screen-state pattern.

---

### Milestone V2.3 G현 Practice History Timeline
Objective:
- Visualize learning journey across sessions.

Scope:
- Introduce module `src/modules/practice-history`
- Add timeline cards/rows for session sequence and trend context.
- Add inferred event badges: improvement, plateau, unlock.

API dependencies:
- `GET /sessions`
- optional curriculum refresh after practice for unlock-event confirmation.

Exit criteria:
- Timeline renders latest sessions with readable score deltas.
- Event badges follow deterministic UI rules and remain read-only.

---

### Milestone V2.4 G현 Technique Visualizer
Objective:
- Make meend and gamak quality visually understandable.

Scope:
- Introduce module `src/modules/technique-visualizer`
- Overlay expected-vs-observed transition rendering.
- Attach technique markers to practice timeline.

API dependencies:
- practice payload `techniques`, `technique_details`.

Exit criteria:
- Meend/gamak regions are rendered when present.
- Empty technique payload shows informative fallback state.

---

### Milestone V2.5 G현 Adaptive Coaching UI
Objective:
- Turn adaptive outputs into actionable practice drills.

Scope:
- Introduce module `src/modules/adaptive-coach`
- Render drill cards:
  - phrase focus
  - tempo target
  - repeat guidance
  - focus instruction
- Integrate data from practice payloads and analytics recommendation into deterministic coaching guidance.

API dependencies:
- practice response `adaptive_plan`
- practice response `song_adaptive_plan.focus_phrase`
- `GET /analytics/recommendation-adaptive_plan`

Exit criteria:
- Coaching panel renders dynamic drill content from backend payload.
- Coaching panel renders deterministic "Next Steps" guidance without LLM dependency.
- Stable fallback behavior when optional payload segments are unavailable.

## 3) Required Frontend Refactors (Shared)
- Expand `src/types/api.ts` for typed radar/history/coach payloads.
- Expand `src/types/normalized.ts` with V2 UI models.
- Extend `src/api/adapters.ts` with V2 normalizers.
- Add V2 hooks under each module and keep page components presentation-focused.
- Update `src/App.tsx` nav to include:
  - Practice Studio
  - Practice History
  - Skill Radar

## 4) Quality Gates Per Milestone
- Contract gate:
  - endpoint compatibility with `docs/API_CONTRACT_V1.md`
- UI gate:
  - loading/error/empty state coverage
- Safety gate:
  - no frontend progression/mastery logic
- Regression gate:
  - v1 pages continue to load and work

## 5) Risk Register
- Radar payload currently excludes direct technique dimension:
  - mitigation: derive short-term from latest session `technique_score`
- Coaching field naming differences across endpoints:
  - mitigation: adapter-level normalization map (`recommended_tempo`/`focus_phrase`/`target_drill`/`variation_strategy`/`tempo_feedback`)
- Optional payload segments may be absent:
  - mitigation: explicit null-safe UI contracts

## 6) Definition of Done (V2 Delivered)
- All V2.1G혀V2.5 milestones implemented and build-validated.
- Practice Studio, Skill Radar, Practice History, Technique Visualizer, and Adaptive Coach shipped in app navigation.
- Adaptive coaching finalized to deterministic next-step guidance (no runtime LLM drill dependency).

## 7) Post-V2 Execution Backlog

### Slice 2 G현 Melody Content Type Foundation
Objective:
- Introduce a dedicated melody content type with explicit contracts and backend domain handling.

Planned outputs:
- Content-type model extension (melody separate from song/alankar)
- Melody practice routing/service path
- Catalog integration contract updates

### Slice 3 G현 Melody Content Expansion Pack
Objective:
- Add first melody content set and integrate into selection/practice flows.

Planned outputs:
- `songs/melody_1.json`
- `songs/melody_2.json`
- `songs/melody_3.json`
- Frontend catalog visibility + practice mode compatibility

### Slice 4 G현 Learning Engine Upgrade (ML-first)
Objective:
- Add model-backed recommendation pipeline using existing session/history data.

Planned outputs:
- Skill profile builder
- Learning difficulty estimator
- Recommendation model training pipeline (offline)
- Model artifact loading at backend startup
- Inference endpoint surface for recommendation outputs

### Slice 5 G현 Frontend Learning-Intelligence Wiring
Objective:
- Surface ML recommendation outputs and melody-type workflows in UI.

Planned outputs:
- Recommendation rendering in learning surfaces
- Difficulty/skill-profile visibility for practice guidance
- Deterministic fallback UI when model output is unavailable

## 8) Locked Decisions (Confirmed 2026-03-04)
- Delivery mode: full-stack incremental by feature slice.
- Melody strategy: new content type (not reused song type).
- Recommendation strategy: ML-first.
- Training data source: existing session/history data only.
- Model serving mode: offline-trained model loaded at backend startup.

## 9) V3 Visualization Execution Sync (Approved 2026-03-05)

### 9.1 Stack Decision
- Chart engine: Apache ECharts.
- React wrapper: `echarts-for-react`.
- Rendering policy: hybrid (retain custom SVG for Practice Studio domain overlays; use ECharts for analytics-heavy surfaces).

### 9.2 Phase 1 G현 Foundation (ECharts Infrastructure)
Objective:
- Establish shared chart infrastructure without UI regression.

Planned outputs:
- Install dependencies: `echarts`, `echarts-for-react`.
- Add shared chart primitives under `frontend/src/modules/charts/`:
  - `echarts.ts` (module registration)
  - `EChartBase.tsx` (shared wrapper)
  - `types.ts`
  - `index.ts`
- Add reusable chart container styles in `frontend/src/styles.css`.

Exit criteria:
- Frontend build passes.
- Existing pages continue to render unchanged.

### 9.3 Phase 2 G현 Skill Radar Migration
Objective:
- Migrate Skill Radar renderer from custom SVG to ECharts radar while keeping the same normalized data semantics.

Planned outputs:
- Add `frontend/src/modules/skill-radar/components/SkillRadarEChart.tsx`.
- Add `frontend/src/modules/skill-radar/options/buildSkillRadarOption.ts`.
- Update `frontend/src/modules/skill-radar/SkillRadarPanel.tsx` to use new renderer.
- Keep existing metric/source cards and fallback behavior.

Exit criteria:
- Skill Radar renders via ECharts using existing normalized payload.
- Build passes with no regression in surrounding pages.

### 9.4 Tracking Reference
- Detailed execution checklist and scope boundaries are maintained in: `Next plan-Analytics_skill_tracking`.
