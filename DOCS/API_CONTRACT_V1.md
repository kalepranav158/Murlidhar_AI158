# API Contract v1 (Frozen)

## Scope
This document freezes frontend-consumed **production** contracts for v1.

- Excludes `/debug/*` from production dependencies.
- Uses `/student/*` wrappers as primary Dashboard/Curriculum/Progress sources.
- Uses `/practice/*`, `/sessions`, `/songs`, and selected `/analytics/*` endpoints as supporting APIs.

## Identity Propagation (v1)
- Method: `user_id` in query/path (no header-based identity in v1).
- Required on all user-scoped endpoints.

## Shared No-Data/Error Envelope (v1)
No-data and recoverable error payloads use:

```json
{
  "status": "no_data" | "error",
  "message": "string",
  "data": null | object,
  "error": "string (optional, for status=error)"
}
```

Backward compatibility: frontend adapters still accept legacy `{ "message": "..." }`.

---

## Frozen Endpoints

### Student (Primary)

#### `GET /student/profile?user_id=...`
- Params: `user_id` (required)
- Success 200:
  - `current_level: string`
  - `unlocked_content: string[]`
  - `mastered_content: string[]`
  - `recommended_content: string | null`
  - `composite_score: number | null`
  - `reason: string | null`
- No-data/Error: envelope above

#### `GET /student/curriculum?user_id=...`
- Params: `user_id` (required)
- Success 200:
  - `current_level: string`
  - `unlocked_content: string[]`
  - `mastered_content: string[]`
  - `locked: string[]`
  - `recommended_content: string | null`
  - `next_goal: string | null`
  - `reason: string | null`
  - `skill_snapshot?: { accuracy?, rhythm_index?, technique_score?, composite_score? }`
- No-data/Error: envelope above

#### `GET /student/analytics?user_id=...`
- Params: `user_id` (required)
- Success 200:
  - `summary?`, `trend?`, `indices?`, `prediction?`, `flags?`, `volatility?`
- No-data/Error: envelope above

#### `GET /student/streak?user_id=...`
- Params: `user_id` (required)
- Success 200:
  - `current_streak: number`
  - `longest_streak: number`
  - `total_practice_days: number`
  - `last_practice_date | last_practice_logical_date: string | null`
- No-data/Error: envelope above

---

### Practice (Primary for practice flow)

#### `POST /practice/alankar/{user_id}/{alankar_id}/{phrase_index}?tempo=60`
- Params: `user_id`, `alankar_id`, `phrase_index` (required path), `tempo` (optional query)
- Multipart: `file` (required)
- Success 200 (shape family):
  - `song`, `phrase_index`, `evaluation`, `adaptive_plan`, `technique_score`, `curriculum`
  - optional: `detected_notes`, `alignment_debug`, `techniques`, `technique_details`
- Error:
  - Validation: `422`
  - Missing content: `404`
  - Processing/other: envelope or HTTP exception detail

#### `POST /practice/song/{user_id}/{song_id}/{phrase_index}?tempo=60`
- Params: `user_id`, `song_id`, `phrase_index` (required), `tempo` optional
- Multipart: `file` (required)
- Success 200:
  - practice payload + `song_adaptive_plan` + `full_song_unlocked`
- Error: as above

#### `POST /practice/song/full/{user_id}/{song_id}`
- Params: `user_id`, `song_id` (required)
- Multipart: `file` (required)
- Success 200:
  - full-song evaluation payload
- Error: as above

---

### Sessions/Songs (Supporting)

#### `GET /sessions/?user_id=...&limit=...`
- Params: `user_id` required, `limit` optional (1..100)
- Success 200:
  - `{ "count": number, "sessions": Session[] }`
- No-data 200:
  - envelope with `status: "no_data"`, `data: { "count": 0, "sessions": [] }`

#### `GET /songs/?content_type=...`
- Params: `content_type` optional (`alankar` | `song` | `melody`)
- Success 200:
  - song list payload (`song_id`, `title`, `tempo`, `phrases`, `content_type`)
- No-data/Error: route-specific payloads (frontend adapters defensive)

#### `GET /songs/{song_id}/phrase/{phrase_index}`
- Params: `song_id` path required, `phrase_index` path required
- Success 200:
  - `song_id: string`
  - `title: string`
  - `content_type: string`
  - `phrase_index: number`
  - `phrase_id: number`
  - `phrase_section: string | null`
  - `phrase_count: number`
  - `reference_tempo: number | null`
  - `notes: Array<{ note: string, time: number }>`
- Error:
  - `404` when content id not found
  - `400` when phrase index is out of range

---

### Analytics (Supporting)

#### `GET /analytics/trend?user_id=...`
- Params: `user_id` required
- Success 200: `{ "accuracy_series": [{ "session": number, "accuracy": number }] }`
- No-data 200: envelope with `status: "no_data"`

#### `GET /analytics/summary?user_id=...`
- Success 200:
  - `total_sessions`, `average_note_accuracy`, `average_pitch_error`, `average_timing_error`, `best_note_accuracy`, `worst_note_accuracy`
- No-data/Error: envelope

#### `GET /analytics/consistency?user_id=...`
- Success 200: `accuracy_standard_deviation`, `consistency_level`
- No-data/Error: envelope

#### `GET /analytics/skill-level?user_id=...`
- Success 200: `skill_level`, averages
- No-data/Error: envelope

#### `GET /analytics/pitch-stability-control?user_id=...`
- Success 200: `average_pitch_error`, `mean_pitch_error`, `pitch_variation`, `pitch_control_level`
- No-data/Error: envelope

#### `GET /analytics/recommendation-adaptive_plan?user_id=...`
- Success 200: `recommended_tempo_adjustment`, `practice_focus`, `suggestion`
- No-data/Error: envelope

#### `GET /analytics/consistency-details?user_id=...`
- Success 200: `accuracy_variation`, `pitch_variation`, `timing_variation`, `primary_instability_source`
- No-data/Error: envelope

#### `GET /analytics/radar?user_id=...`
- Success 200: radar payload (service-provided)
- Error 200 envelope: `status: "error"`, `message`, optional `error`

#### `GET /analytics/skill-evolution?user_id=...`
- Success 200: evolution payload
- No-data/Error: envelope

#### `GET /analytics/risk?user_id=...`
- Success 200: risk payload
- Error: envelope

#### `GET /analytics/forecast?user_id=...`
- Success 200: forecast payload
- Error: envelope

#### `GET /analytics/song/weakest-phrase?user_id=...&song_id=...`
- Params: `user_id`, `song_id` required
- Success 200: `{ phrase_id, avg_accuracy, attempts }`
- No-data/Error: envelope

---

## HTTP Status Notes (v1)
- Most no-data outcomes currently return **200** with no-data envelope.
- Validation errors are framework-native **422**.
- Explicit missing resources may return **404** where raised.
- Transport/server errors may return **5xx**; frontend must keep retry/error UI behavior.

## Frontend Adapter Requirements (frozen)
- Must support:
  - success payloads
  - shared envelope (`status/message/data/error`)
  - legacy `{ message }` fallback
- Must normalize optional/null fields to stable UI-safe defaults.
