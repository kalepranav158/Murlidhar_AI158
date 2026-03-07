import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

import database.db as db
from app.routes import analytics as analytics_route
from app.routes import debug as debug_route
from app.routes import sessions as sessions_route
from app.routes import songs as songs_route
from app.routes import student as student_route


def _build_client(router) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _assert_no_data_envelope(payload: dict, message: str):
    assert payload.get("status") == "no_data"
    assert payload.get("message") == message
    assert "data" in payload


def test_sessions_no_data_envelope(monkeypatch):
    monkeypatch.setattr(sessions_route, "get_sessions", lambda user_id, limit: [])

    client = _build_client(sessions_route.router)
    response = client.get("/sessions/", params={"user_id": "user_x", "limit": 5})

    assert response.status_code == 200
    payload = response.json()
    _assert_no_data_envelope(payload, "No sessions available.")
    assert payload["data"] == {"count": 0, "sessions": []}


def test_student_analytics_no_data_envelope(monkeypatch):
    monkeypatch.setattr(student_route, "compute_analytics", lambda user_id: None)

    client = _build_client(student_route.router)
    response = client.get("/student/analytics", params={"user_id": "user_x"})

    assert response.status_code == 200
    payload = response.json()
    _assert_no_data_envelope(payload, "Not enough sessions.")


def test_analytics_trend_no_data_envelope(monkeypatch):
    monkeypatch.setattr(
        analytics_route,
        "get_sessions",
        lambda user_id, limit: [
            {
                "note_accuracy": 88,
                "avg_pitch_error": 7,
                "avg_timing_error": 0.2,
            }
        ],
    )

    client = _build_client(analytics_route.router)
    response = client.get("/analytics/trend", params={"user_id": "user_x"})

    assert response.status_code == 200
    payload = response.json()
    _assert_no_data_envelope(payload, "Not enough sessions.")


def test_analytics_radar_error_envelope(monkeypatch):
    def _raise_error(user_id: str):
        raise RuntimeError("simulated radar failure")

    monkeypatch.setattr(analytics_route, "build_latest_radar", _raise_error)

    client = _build_client(analytics_route.router)
    response = client.get("/analytics/radar", params={"user_id": "user_x"})

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "error"
    assert payload.get("message") == "Error generating radar data"
    assert "simulated radar failure" in payload.get("error", "")


def test_debug_alankar_no_data_envelope(monkeypatch, tmp_path: Path):
    test_db = tmp_path / "debug_contract_test.db"
    conn = sqlite3.connect(str(test_db))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS skill_progress (
            user_id TEXT,
            skill_id TEXT,
            skill_type TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(db, "DB_NAME", str(test_db))

    client = _build_client(debug_route.router)
    response = client.get("/debug/alankar/user_x/alankar_1")

    assert response.status_code == 200
    payload = response.json()
    _assert_no_data_envelope(payload, "No skill_progress record found")


def test_songs_phrase_reference_success_shape():
    client = _build_client(songs_route.router)
    response = client.get("/songs/song_1/phrase/0")

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("song_id") == "song_1"
    assert payload.get("phrase_index") == 0
    assert isinstance(payload.get("phrase_count"), int)
    assert isinstance(payload.get("notes"), list)
    assert payload["notes"], "expected phrase notes in response"


def test_songs_phrase_reference_invalid_phrase_index():
    client = _build_client(songs_route.router)
    response = client.get("/songs/song_1/phrase/9999")

    assert response.status_code == 400
    payload = response.json()
    assert payload.get("detail") == "Invalid phrase index"
