# Frontend V2 Implementation Plan (Synced)

Status: Implemented and synchronized (created 2026-03-04)

This plan is sequenced to match the approved V2 rollout order and current backend contracts.

## 0) Implementation Status
- [x] Milestone V2.1 — Practice Studio visualization
- [x] Milestone V2.2 — Skill Radar chart
- [x] Milestone V2.3 — Practice History timeline
- [x] Milestone V2.4 — Technique Visualizer
- [x] Milestone V2.5 — Adaptive Coaching UI

## 1) Execution Order (Approved)
1. Practice Studio visualization
2. Skill Radar chart
3. Practice History timeline
4. Technique Visualizer
5. Adaptive Coaching UI

## 2) Milestone Plan

### Milestone V2.1 — Practice Studio Visualization
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

### Milestone V2.2 — Skill Radar Chart
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

### Milestone V2.3 — Practice History Timeline
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

### Milestone V2.4 — Technique Visualizer
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

### Milestone V2.5 — Adaptive Coaching UI
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
  - endpoint compatibility with `DOCS/API_CONTRACT_V1.md`
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

## 6) Definition of Done (V2 Planning Stage)
- Architecture defined and documented.
- Phased implementation sequence locked.
- Contract mappings documented by feature.
- Existing docs synchronized with this plan.

Implementation begins only when explicitly requested.
