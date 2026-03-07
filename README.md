# VENORA

VENORA is an AI-assisted flute learning platform with a FastAPI backend and a React + Vite frontend. It evaluates practice audio, tracks progression and streaks, generates analytics, and supports guided practice flows.

Repository folder naming convention: keep the project root folder as `VENORA`.

## Repository Structure

```text
backend/      FastAPI app, services, models, utility modules
data/         Song catalog, knowledge corpus, db artifacts, vector db
docs/         Architecture, API contract, implementation notes
frontend/     React + TypeScript client
tests/        Freeze, regression, and legacy test suites
```

## Tech Stack

- Backend: Python, FastAPI
- Frontend: React, TypeScript, Vite
- Storage: SQLite
- Audio/Scoring: aubio, NumPy-based processing, DTW
- LLM/RAG: LangChain + Google GenAI + Chroma

## Quick Start

### 1. Backend Setup

```bash
# Optional: create env once (skip if you already have one)
conda create -n venora python=3.10 -y

# Activate your conda env (example: gokul)
conda activate gokul

pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Backend API default URL: `http://127.0.0.1:8000`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL: `http://127.0.0.1:5173`

### 3. Run Frontend + Backend Together (from `frontend/`)

```bash
npm run dev:all
```

## Environment Variables

- `DEBUG_ENDPOINTS` controls debug routes. Default: `false` (recommended for release).
- Set `DEBUG_ENDPOINTS=true` only for local debugging.
- `GOOGLE_API_KEY` is required for LLM-backed routes.
- `VENORA_AUTH_USERNAME` overrides login username (default: `gokul`).
- `VENORA_AUTH_PASSWORD` overrides login password (default: `venora123`).
- `VENORA_AUTH_TOKEN_TTL_MINUTES` sets auth token lifetime (default: `480`).
- `VENORA_GOOGLE_CLIENT_ID` enables backend Google token verification for sign-in.
- `VENORA_GOOGLE_CLIENT_IDS` optionally allows multiple backend Google client IDs (comma-separated).
- `VENORA_GOOGLE_ALLOWED_DOMAIN` optionally restricts Google sign-in to one domain (example: `company.com`).
- `VENORA_GOOGLE_ALLOWED_EMAILS` optionally restricts Google sign-in to a comma-separated email allowlist.
- `VENORA_GOOGLE_CLOCK_SKEW_SECONDS` allows small local clock drift for Google token verification (default: `30`, max: `300`).
- `VENORA_AUTH_DEBUG` controls detailed backend auth errors. Default: `false`.
- Set `VENORA_AUTH_DEBUG=true` only for local debugging.
- `VITE_GOOGLE_CLIENT_ID` enables the Google button in the frontend login page.

## Authentication

- Open the frontend and sign in before using the dashboard.
- Recommended authentication mode: Google Sign-In.
	- Add your Google OAuth Web client ID to backend env: `VENORA_GOOGLE_CLIENT_ID=<your-client-id>`
	- Add the same value in `frontend/.env`: `VITE_GOOGLE_CLIENT_ID=<your-client-id>`
	- Restart backend and frontend.

- Password login is an optional local fallback.
	- Backend reads `VENORA_AUTH_USERNAME` and `VENORA_AUTH_PASSWORD`.
	- If not set, fallback defaults are `gokul` / `venora123`.
	- If your project standard username is `kalepranav158`, set `VENORA_AUTH_USERNAME=kalepranav158` in environment.

## Validation

```bash
python freeze_audit.py
python -m pytest tests -q
cd frontend && npm run build
```

## Notes

- Audio-device tests are manual by default. Set `RUN_AUDIO_DEVICE_TESTS=1` to enable them.
- Some legacy LLM smoke checks are intentionally skipped in automated runs.
