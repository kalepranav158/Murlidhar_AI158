# Frontend Architecture V2 (Implemented)

Status: Implemented and synchronized; post-V2 V3-visualization track aligned (updated 2026-03-05)

## 1) Goal
Transform frontend from a scorecard UI into an interactive AI music tutor, while preserving all v1 contract guardrails.

V2 outcome:
- Interactive practice studio visualization
- Technique execution understanding
- Radar-based skill balance view
- Session-history learning context
- Adaptive drill coaching UI

## 2) Non-Negotiable Constraints
- Keep v1 backend contracts stable (`docs/API_CONTRACT_V1.md`).
- Do not move progression logic to frontend.
- Continue envelope-safe handling (`status/message/data/error`).
- Keep user identity propagation as `user_id` query/path.
- No production dependency on `/debug/*`.

## 3) Current Baseline (Post-V2)
- Pages in `frontend/src/pages`: Dashboard, Practice Studio, Curriculum, Progress, Practice History, Skill Radar, Ask Guru, Diagnostics (internal).
- V2 modules are implemented under `frontend/src/modules`:
  - `practice-studio`
  - `skill-radar`
  - `practice-history`
  - `technique-visualizer`
  - `adaptive-coach`
- Practice API returns rich payload fields:
  - `detected_notes`
  - `alignment_debug`
  - `techniques`
  - `technique_details`
  - `adaptive_plan`
  - `song_adaptive_plan`
- Analytics supports radar/trend, adaptive recommendation, and learning-intelligence endpoints.
- Sessions API supports timeline source data (`timestamp`, scores, indices).

## 4) V2 Frontend Module Topology
Add modular vertical slices under:

`frontend/src/modules/`
- `practice-studio/`
- `technique-visualizer/`
- `skill-radar/`
- `practice-history/`
- `adaptive-coach/`

Each module should contain:
- `components/`
- `hooks/`
- `types.ts`
- `mappers.ts` (API GÂ∆ UI model)
- `index.ts`

Shared primitives remain in:
- `frontend/src/components`
- `frontend/src/api`
- `frontend/src/types`

## 5) V2 Page Structure
Target top-level views:
- Dashboard
- Practice Studio
- Curriculum
- Progress
- Practice History
- Skill Radar
- Ask Guru
- Diagnostics (optional/internal)

Migration note:
- Replace current `PracticePage` UX with Practice Studio container.
- Keep existing Dashboard/Curriculum/Progress stable while incrementally adding V2 views.

## 6) Data Contract Mapping (V2)

### 6.1 Practice Studio
Sources:
- `POST /practice/alankar/{user_id}/{alankar_id}/{phrase_index}`
- `POST /practice/song/{user_id}/{song_id}/{phrase_index}`

Required payload fields:
- `detected_notes[]` for user pitch curve points (`time`, `cents`, `note`)
- `alignment_debug.dtw_transposition_shift_semitones`
- `evaluation` metrics
- `techniques` (raw detection)
- `technique_details` (comparison details)

Planned component set:
- `PitchTimeline`
- `ReferenceNoteBar`
- `UserPitchCurve`
- `TechniqueMarker`

### 6.2 Technique Visualizer
Primary source:
- `techniques` + `technique_details` in practice response

Secondary source:
- phrase transition metadata (already available to backend from song/alankar content)

Expected visual use-cases:
- Meend glide continuity (expected vs observed)
- Gamak oscillation region highlighting

### 6.3 Skill Radar
Source:
- `GET /analytics/radar?user_id=...`

Current backend response fields:
- `pitch`
- `rhythm`
- `consistency`
- `composite`

V2 target dimensions:
- Pitch
- Rhythm
- Technique
- Consistency
- Progress

Normalization rule (initial):
- `technique`: derive from latest session `technique_score` (sessions endpoint) until radar includes technique directly
- `progress`: map from normalized composite trend slope or current composite snapshot

### 6.4 Practice History Timeline
Source:
- `GET /sessions/?user_id=...&limit=...`

Session fields available now:
- `timestamp`, `note_accuracy`, `composite_score`, indices, `technique_score`

Timeline event derivation (frontend read-only):
- Improvement: positive delta above threshold across recent sessions
- Plateau: low change across configured window
- Unlock event: infer from curriculum delta after practice refresh, not local progression logic

### 6.5 Adaptive Coaching UI
Primary sources:
- practice response `adaptive_plan`
- practice response `song_adaptive_plan.focus_phrase`
- analytics recommendation API: `GET /analytics/recommendation-adaptive_plan`

Field mapping:
- Tempo adjustment: `adaptive_plan.recommended_tempo` (numeric) and/or analytics recommendation text
- Focus phrase: `song_adaptive_plan.focus_phrase`
- Deterministic next steps: adapter-derived from `target_drill`, `variation_strategy`, `tempo_feedback`, `focus_area`, plus analytics recommendation text

## 7) Internal Frontend Data Flow (V2)
Practice Recording/Upload
GÂ∆ Practice API evaluation
GÂ∆ Practice Studio visualization update
GÂ∆ Technique visualization overlay
GÂ∆ Radar refresh
GÂ∆ Adaptive coach drill cards + deterministic next steps

This preserves backend authority while improving learning UX feedback loops.

## 8) State & Adapter Strategy
- Extend `frontend/src/types/api.ts` with typed radar/coaching payloads.
- Extend `frontend/src/types/normalized.ts` with V2-specific normalized models.
- Add adapter functions in `frontend/src/api/adapters.ts`:
  - `normalizeRadar(...)`
  - `normalizePracticeHistory(...)`
  - `normalizeAdaptiveCoach(...)`
- Keep UI components consuming normalized shapes only.

## 9) UI/UX Architecture Principles for V2
- Show both reference and observed performance together.
- Render immediate contextual feedback near timeline markers.
- Preserve existing loading/error/empty states on each module.
- Avoid introducing client-side unlock/mastery calculations.
- Keep fallback rendering when optional practice payload fields are missing.
- Keep adaptive coaching deterministic in the frontend (no runtime LLM dependency for drill generation).

## 10) Delivery Scope Boundary
In-scope for V2 frontend architecture:
- New module structure
- New visualization components
- New page wiring
- Adapter + hook expansion

Out-of-scope for this phase:
- Backend contract breakage
- Progression rule changes
- Schema migrations in DB

## 11) Cross-Document Alignment
This architecture is synchronized with:
- `docs/API_CONTRACT_V1.md`
- `docs/FRONTEND_V1_IMPLEMENTATION_CHECKLIST.md`
- `docs/ARCHITECTURE.md`
- `docs/CHANGELOG.md`
- `sprint/CURRENT_SPRINT.md`

## 12) Post-V2 Architecture Track (Approved)

### 12.1 Melody Content Domain (new type)
- Add melody as a dedicated content type (not an alias of existing song type).
- Extend catalog/content contracts to carry explicit content typing.
- Add melody practice path with phrase-level handling while keeping existing song/alankar flows stable.

### 12.2 Learning Engine Upgrade (ML-first)
- Add backend components:
  - skill profile builder
  - learning difficulty estimator
  - recommendation model runner
- Train using existing session/history data.
- Persist model artifact offline and load it at backend startup for inference.

### 12.3 Inference Surface + Frontend Wiring
- Expose recommendation/skill-profile/difficulty inference outputs through backend APIs.
- Render model outputs in frontend learning surfaces with deterministic fallback states.
- Preserve no-frontend-progression-logic constraint while enriching guidance UX.

## 13) V3 Visualization Execution Track (Approved 2026-03-05)

### 13.1 Chart Engine Decision
- Primary chart engine: Apache ECharts.
- React integration: `echarts-for-react`.
- Rationale: strongest fit for radar + heatmap + diagnostics visualization while preserving incremental delivery.

### 13.2 Hybrid Rendering Strategy
- Keep current custom SVG domain overlays in Practice Studio (`PitchTimeline`, markers, reference/user curve).
- Use ECharts for analytics-first surfaces (Skill Radar migration first, then Progress and internal Diagnostics charts).
- Keep Diagnostics internal and non-blocking for public learner workflows.

### 13.3 Phase Execution (Immediate)
- Phase 1 (foundation): install/chart wrapper infrastructure under `frontend/src/modules/charts`.
- Phase 2 (migration): move Skill Radar renderer from custom SVG to ECharts, preserving existing normalized data contract and source labels.

### 13.4 Source of Truth
- Execution blueprint is maintained in root planning document: `Next plan-Analytics_skill_tracking`.
