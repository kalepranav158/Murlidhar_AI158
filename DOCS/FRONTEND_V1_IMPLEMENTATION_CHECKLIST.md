# Frontend v1 Implementation Checklist (Contract-First)

## 0) Scope Guardrails (Do Not Violate)
- Frontend is display-only for progression outcomes.
- No unlock/mastery/streak/composite calculations in UI.
- Do not depend on `/debug/*` for production.
- v1 audio path supports **file upload and live recording**. Uploaded/recorded audio is converted to WAV before processing.

### v2 Continuation References
- `DOCS/FRONTEND_ARCHITECTURE_V2.md`
- `DOCS/FRONTEND_V2_IMPLEMENTATION_PLAN.md`

---

## 1) Current Backend Endpoint Inventory (Verified)

### Practice (production)
- `POST /practice/alankar/{user_id}/{alankar_id}/{phrase_index}`
  - Query: `tempo` (default 60)
  - Multipart: `file`
  - Returns: `PracticeResponse`-like payload with `evaluation`, `adaptive_plan`, `technique_score`, `curriculum`, etc.
- `POST /practice/song/{user_id}/{song_id}/{phrase_index}`
  - Query: `tempo` (default 60)
  - Multipart: `file`
  - Returns: phrase-level song practice payload + `song_adaptive_plan` + `full_song_unlocked`.
- `POST /practice/practice/song/full/{user_id}/{song_id}`
  - Multipart: `file`
  - Returns: full-song evaluation payload.
  - Note: path currently contains duplicated `practice` segment by route declaration.

### Analytics (production)
- `GET /analytics/summary?user_id=...`
- `GET /analytics/trend?user_id=...`
- `GET /analytics/skill-level?user_id=...`
- `GET /analytics/consistency?user_id=...`
- `GET /analytics/pitch-stability-control?user_id=...`
- `GET /analytics/recommendation-adaptive_plan?user_id=...`
- `GET /analytics/consistency-details?user_id=...`
- `GET /analytics/dashboard?user_id=...`
- `GET /analytics/test-dashboard?user_id=...` (test-only)
- `GET /analytics/analytics/radar?user_id=...` (double analytics segment)
- `GET /analytics/skill-evolution?user_id=...`
- `GET /analytics/risk?user_id=...`
- `GET /analytics/forecast?user_id=...`
- `GET /analytics/song/weakest-phrase?user_id=...&song_id=...`

### Sessions/Songs (production)
- `GET /sessions/?user_id=...&limit=...`
- `GET /songs/`

### Student wrappers (production, newly added)
- `GET /student/profile?user_id=...`
- `GET /student/curriculum?user_id=...`
- `GET /student/analytics?user_id=...`
- `GET /student/streak?user_id=...`

### Debug (non-production dependency)
- `GET /debug/sessions/{user_id}`
- `GET /debug/alankar/{user_id}/{alankar_id}`
- `GET /debug/phrase/{user_id}/{song_id}/{phrase_id}`
- `GET /debug/analytics/{user_id}`
- `GET /debug/student/{user_id}`
- Enabled only when `DEBUG_ENDPOINTS=true`.

---

## 2) Phase 0 Contract Freeze (Required Before UI Build)
- [x] Freeze **v1 frontend-consumed endpoints** (non-debug only).
- [x] Production wrappers available:
  - [x] `GET /student/profile`
  - [x] `GET /student/curriculum`
  - [x] `GET /student/analytics`
  - [x] `GET /student/streak`
- [x] Wrappers mapped to existing production services (not debug routes).
- [x] For each chosen endpoint, freeze:
  - [x] Required params and identity propagation method
  - [x] Success payload schema
  - [x] Message-only / no-data fallback payload
  - [x] Error payload and status codes

Contract reference: `DOCS/API_CONTRACT_V1.md`.

**Decision note:** Frontend should default to `/student/*` wrappers for profile/curriculum/analytics/streak and use `/practice/*`, `/sessions`, `/songs` as supporting APIs.

---

## 3) Frontend API Adapter Plan (Normalization Layer)

Create `src/api/adapters.ts` and normalize all backend responses into stable frontend types.

### 3.1 Normalized Types (frontend-owned)
- [x] `StudentProfileNormalized`
  - `currentLevel: string`
  - `unlockedContent: string[]`
  - `masteredContent: string[]`
  - `recommendedContent: string | null`
  - `compositeScore: number | null`
- [x] `PracticeResultNormalized`
  - `noteAccuracy: number | null`
  - `avgPitchErrorCents: number | null`
  - `avgTimingErrorSec: number | null`
  - `rhythmStability: number | null`
  - `techniqueScore: number | null`
  - `adaptivePlanSummary: string | null`
  - `unlockEvent: boolean`
  - `rawFeedback: unknown`
- [x] `AnalyticsSnapshotNormalized`
  - `compositeTrend: number[]`
  - `slope: number | null`
  - `consistencyIndex: number | null`
  - `streakCurrent: number | null`
  - `streakLongest: number | null`

### 3.2 Defensive Rules
- [x] Treat `{ message: string }` as valid no-data state, not crash path.
- [x] Provide null/default values for missing optional fields.
- [x] Keep unknown raw payload attached for diagnostics.
- [x] Page components consume normalized objects only.

### 3.3 Hooks Layer (Aligned to Plan)
- [x] `useStudentProfile.ts` implemented
- [x] `usePracticeSession.ts` implemented
- [x] `useAnalytics.ts` implemented

---

## 4) API Client Concerns (Cross-Cutting v1)
- [x] `src/api/client.ts` with:
  - [x] `API_BASE_URL` from env (`VITE_API_BASE_URL` or equivalent)
  - [x] Timeout defaults
  - [x] Optional retry for idempotent `GET`
  - [x] Centralized transport + API error mapping
- [x] Identity propagation strategy (choose one and enforce globally):
  - [x] User id in path/query
  - [ ] Header/token-based identity
- [x] Screen-state model everywhere:
  - [x] Loading state
  - [x] Error state + retry action
  - [x] Empty state (message/no sessions/no analytics)

---

## 5) Milestone Execution Order (Implementation)

### Milestone 0 — Contract Freeze
- [x] Final endpoint shortlist and schema document signed off.
- Exit criteria:
  - [x] Core v1 pages do not require `/debug/*` (debug kept in diagnostics page only).

### Milestone 1 — API Adapter Foundation
- [x] Implemented `client.ts`, `types/normalized.ts`, `api/adapters.ts`.
- [x] Added endpoint modules (`practice.ts`, `analytics.ts`, `sessions.ts`, `songs.ts`) plus `student.ts`, `ask.ts`, `debug.ts`, `system.ts`.
- Exit criteria:
  - [x] App renders normalized responses from live backend.

### Milestone 2 — Practice Page
- [x] File upload + live recording flow to `/practice/*` endpoints.
- [x] Practice page renders backend-driven metrics only.
- [x] Curriculum snapshot and unlock signals come from backend response.
- Exit criteria:
  - [x] Handles success + message-only + transport errors without crashes.

### Milestone 3 — Dashboard Page
- [x] Render current level, streak, composite snapshot, recommendation.
- [x] Compose primarily from normalized `/student/profile`, `/student/analytics`, `/student/streak`.
- Exit criteria:
  - [x] Fully functional without debug endpoints.

### Milestone 4 — Progress Page
- [x] Composite/trend/consistency indicators implemented.
- [x] Uses analytics + trend data through adapters/API layer.
- Exit criteria:
  - [x] Sparse/empty datasets handled through screen states.

### Milestone 5 — Curriculum Page
- [x] Render unlocked/locked/mastered/next-goal from backend snapshot.
- Exit criteria:
  - [x] No client-side mastery progression logic present.

---

## 6) Backend Follow-Ups (Recommended Before UI Finalization)
- [x] Added clean production wrappers under `/student/*`.
- [x] Normalize path naming oddities for future stability:
  - [x] `/practice/practice/song/full/...` (normalized alias `/practice/song/full/...` added)
  - [x] `/analytics/analytics/radar` (normalized alias `/analytics/radar` added)
- [x] Standardized no-data/error responses to a shared envelope shape across route modules (`analytics`, `student`, `sessions`, `debug`).
- [x] Added contract regression tests for envelope behavior on key routes (`tests/test_api_contract_v1.py`).

---

## 6.1) Content Catalog Sync (Songs / Alankars)
- [x] `songs/alankar_1.json` aligned to beginner warmup progression pattern.
- [x] `songs/alankar_2.json` added using existing phrase-note JSON schema.
- [x] `songs/alankar_3.json` added using existing phrase-note JSON schema.
- [x] `songs/alankar_4.json` added using existing phrase-note JSON schema.
- [x] `songs/alankar_5.json` added using existing phrase-note JSON schema.
- [x] `songs/alankar_6.json` added using existing phrase-note JSON schema.
- [x] `songs/alankar_7.json` added using existing phrase-note JSON schema.
- [x] `songs/alankar_8.json` added using existing phrase-note JSON schema.
- [x] `songs/alankar_9.json` added using existing phrase-note JSON schema.
- [x] `songs/alankar_10.json` added using existing phrase-note JSON schema.
- [x] Unlock chain continuity completed across beginner pack (`alankar_1` → `alankar_10`).

---

## 7) Definition of Done (v1)
- [x] All four pages implemented: Dashboard, Practice, Progress, Curriculum.
- [x] No debug endpoint dependency in core production pages.
- [x] One adapter layer between UI and backend contracts.
- [x] All pages include loading/error/empty states.
- [x] No frontend progression logic (unlock/mastery/streak/composite).
- [x] Env-based API URL and consistent identity propagation are documented and enforced.
