import json
import importlib
import os
import sqlite3
import uuid
from datetime import datetime

import pytest

import database.db as db
from app.services.adaptive_engine import build_snapshot
from app.services.analytics_engine import compute_analytics
from app.services.curriculum_service import evaluate_curriculum_progress
from database.db import (
    compute_session_hash,
    get_practice_streak,
    init_db,
    prune_analytics_window,
    save_analytics_snapshot,
    save_session,
    update_practice_streak,
    update_skill_progress,
    verify_unlock_integrity,
)

SKILL_TYPE = "alankar"
THRESHOLD = 0.75


def _assert_not_live_db(path: str):
    if os.path.basename(path).lower() == "practice_data.db":
        raise RuntimeError("Refusing to run tests against live Practice_data.db")


@pytest.fixture(autouse=True)
def setup_test_db():
    test_db = f"test_backend_freeze_{uuid.uuid4().hex}.db"
    _assert_not_live_db(test_db)
    db.DB_NAME = test_db
    init_db(test_db)
    yield
    try:
        os.remove(test_db)
    except OSError:
        pass


def _seed_curriculum_files(skill_id: str, next_skill_id: str):
    with open(f"songs/{skill_id}.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "id": skill_id,
                "type": "alankar",
                "level": "beginner",
                "required_accuracy": 80,
                "required_rhythm_index": 0.6,
                "required_technique_score": 0.0,
                "unlock_next": next_skill_id,
                "phrases": [{"phrase_id": 1, "notes": ["Sa", "Re", "Ga"]}],
            },
            handle,
        )

    with open(f"songs/{next_skill_id}.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "id": next_skill_id,
                "type": "alankar",
                "level": "beginner",
                "required_accuracy": 80,
                "required_rhythm_index": 0.6,
                "required_technique_score": 0.0,
                "unlock_next": None,
                "phrases": [{"phrase_id": 1, "notes": ["Ga", "Re", "Sa"]}],
            },
            handle,
        )


def _remove_curriculum_files(*paths: str):
    for file_name in paths:
        try:
            os.remove(file_name)
        except OSError:
            pass


def test_freeze_full_integration_chain():
    user_id = "freeze_user_1"
    skill_id = "freeze_alankar_1"
    next_skill_id = "freeze_alankar_2"
    _seed_curriculum_files(skill_id, next_skill_id)

    reference = ["Sa", "Re", "Ga"]
    played = [{"note": "Sa", "cents": 0.0, "time": 0.0}]

    try:
        for index in range(3):
            payload = {
                "note_accuracy": 90,
                "avg_pitch_error_cents": 5,
                "avg_timing_error_sec": 0.1,
                "mistakes": [],
                "composite_score": 0.88 + (index * 0.01),
                "pitch_index": 0.9,
                "rhythm_index": 0.9,
                "consistency_index": 1.0,
                "technique_score": 0.8,
            }

            saved = save_session(user_id, reference, played, payload, skill_id=skill_id)
            assert saved is not None
            assert saved["status"] == "saved"

            skill_hash = compute_session_hash(user_id, skill_id, f"audio_{index}")
            progress = update_skill_progress(
                user_id,
                skill_id,
                SKILL_TYPE,
                0.88,
                THRESHOLD,
                session_hash=skill_hash,
            )

        assert progress["unlocked_now"] is True
        assert progress["is_unlocked"] is True
        assert progress["successful_sessions"] == 3

        curriculum = evaluate_curriculum_progress(user_id)
        assert skill_id in curriculum["mastered_content"]
        assert next_skill_id in curriculum["unlocked_content"]

        streak = update_practice_streak(user_id, current_date=datetime(2026, 3, 1, 10, 0, 0))
        assert streak["current_streak"] == 1

        analytics = compute_analytics(user_id)
        assert analytics is not None
        save_analytics_snapshot(user_id, build_snapshot(analytics))

        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM analytics_snapshots WHERE user_id = ?",
            (user_id,),
        )
        snapshot_count = cursor.fetchone()[0]
        conn.close()

        assert snapshot_count >= 1
    finally:
        _remove_curriculum_files(f"songs/{skill_id}.json", f"songs/{next_skill_id}.json")


def test_duplicate_submission_stress_idempotent():
    user_id = "freeze_user_2"
    skill_id = "freeze_skill_2"

    reference = ["Sa", "Re"]
    played = [{"note": "Sa", "cents": 0.0, "time": 0.0}]
    payload = {
        "note_accuracy": 80,
        "avg_pitch_error_cents": 7,
        "avg_timing_error_sec": 0.2,
        "mistakes": [],
        "composite_score": 0.8,
        "pitch_index": 0.8,
        "rhythm_index": 0.8,
        "consistency_index": 1.0,
        "technique_score": 0.7,
    }

    first_save = save_session(user_id, reference, played, payload, skill_id=skill_id)
    second_save = save_session(user_id, reference, played, payload, skill_id=skill_id)

    assert first_save is not None
    assert second_save is not None
    assert first_save["status"] == "saved"
    assert second_save["status"] == "duplicate_rejected"

    session_hash = compute_session_hash(user_id, skill_id, "same_audio")
    first_progress = update_skill_progress(
        user_id,
        skill_id,
        SKILL_TYPE,
        0.8,
        THRESHOLD,
        session_hash=session_hash,
    )
    second_progress = update_skill_progress(
        user_id,
        skill_id,
        SKILL_TYPE,
        0.82,
        THRESHOLD,
        session_hash=session_hash,
    )

    assert first_progress["duplicate"] is False
    assert second_progress["duplicate"] is True
    assert second_progress["successful_sessions"] == first_progress["successful_sessions"]


def test_save_session_updates_streak_state():
    user_id = "freeze_user_streak_auto"
    skill_id = "freeze_skill_streak_auto"

    reference = ["Sa", "Re"]
    played = [{"note": "Sa", "cents": 0.0, "time": 0.0}]
    payload = {
        "note_accuracy": 84,
        "avg_pitch_error_cents": 6,
        "avg_timing_error_sec": 0.2,
        "mistakes": [],
        "composite_score": 0.81,
        "pitch_index": 0.8,
        "rhythm_index": 0.8,
        "consistency_index": 1.0,
        "technique_score": 0.7,
    }

    saved = save_session(user_id, reference, played, payload, skill_id=skill_id)

    assert saved["status"] == "saved"
    streak = get_practice_streak(user_id)
    assert streak["current_streak"] == 1
    assert streak["longest_streak"] == 1
    assert streak["total_practice_days"] == 1


def test_get_practice_streak_backfills_from_existing_sessions():
    user_id = "freeze_user_streak_backfill"

    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sessions (
            user_id, timestamp, reference, played_notes,
            note_accuracy, avg_pitch_error, avg_timing_error,
            mistakes, composite_score, pitch_index,
            rhythm_index, consistency_index, technique_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            "2026-03-01T10:00:00",
            "[]",
            "[]",
            80.0,
            5.0,
            0.2,
            "[]",
            0.8,
            0.8,
            0.8,
            1.0,
            0.6,
        ),
    )
    cursor.execute(
        """
        INSERT INTO sessions (
            user_id, timestamp, reference, played_notes,
            note_accuracy, avg_pitch_error, avg_timing_error,
            mistakes, composite_score, pitch_index,
            rhythm_index, consistency_index, technique_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            "2026-03-02T11:00:00",
            "[]",
            "[]",
            85.0,
            4.0,
            0.15,
            "[]",
            0.85,
            0.85,
            0.85,
            1.0,
            0.7,
        ),
    )
    conn.commit()
    conn.close()

    streak = get_practice_streak(user_id)

    assert streak["current_streak"] == 2
    assert streak["longest_streak"] == 2
    assert streak["total_practice_days"] == 2


def test_unlock_integrity_audit_all_skills():
    user_id = "freeze_user_3"
    skills = ["freeze_skill_3_a", "freeze_skill_3_b", "freeze_skill_3_c"]

    for skill_id in skills:
        for i in range(3):
            update_skill_progress(
                user_id,
                skill_id,
                SKILL_TYPE,
                0.85,
                THRESHOLD,
                session_hash=compute_session_hash(user_id, skill_id, f"ok_{i}"),
            )

    for skill_id in skills:
        audit = verify_unlock_integrity(user_id, skill_id)
        assert audit["valid"] is True
        assert audit["issues"] == []


def test_analytics_window_max_30_prunes_oldest_first():
    user_id = "freeze_user_4"
    skill_id = "freeze_skill_4"

    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    for i in range(35):
        cursor.execute(
            """
            INSERT INTO analytics_snapshots (
                user_id, skill_id, session_id, timestamp,
                accuracy_score, timing_score, technique_score, composite_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, skill_id, i, datetime.now().isoformat(), 80.0, 80.0, 0.8, 0.8),
        )
    conn.commit()
    conn.close()

    prune_analytics_window(user_id, skill_id, max_window=30)

    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM analytics_snapshots WHERE user_id = ? AND skill_id = ?",
        (user_id, skill_id),
    )
    count_after = cursor.fetchone()[0]

    cursor.execute(
        "SELECT MIN(session_id), MAX(session_id) FROM analytics_snapshots WHERE user_id = ? AND skill_id = ?",
        (user_id, skill_id),
    )
    oldest_session_id, newest_session_id = cursor.fetchone()
    conn.close()

    assert count_after == 30
    assert oldest_session_id == 5
    assert newest_session_id == 34


def test_streak_boundary_simulation():
    user_id = "freeze_user_5"

    same_day_1 = datetime(2026, 3, 1, 8, 0, 0)
    same_day_2 = datetime(2026, 3, 1, 20, 0, 0)
    next_day = datetime(2026, 3, 2, 10, 0, 0)
    two_day_gap = datetime(2026, 3, 4, 10, 0, 0)

    first = update_practice_streak(user_id, current_date=same_day_1)
    second = update_practice_streak(user_id, current_date=same_day_2)
    third = update_practice_streak(user_id, current_date=next_day)
    fourth = update_practice_streak(user_id, current_date=two_day_gap)

    assert first["current_streak"] == 1
    assert second["current_streak"] == 1
    assert third["current_streak"] == 2
    assert fourth["current_streak"] == 1


def test_basic_load_simulation_20_sessions():
    user_id = "freeze_user_6"
    skill_id = "freeze_skill_6"

    last_result = None
    for i in range(20):
        last_result = update_skill_progress(
            user_id,
            skill_id,
            SKILL_TYPE,
            0.81,
            THRESHOLD,
            session_hash=compute_session_hash(user_id, skill_id, f"load_{i}"),
        )
        assert last_result["duplicate"] is False

    assert last_result is not None
    assert last_result["successful_sessions"] == 20
    assert last_result["is_unlocked"] is True


def test_debug_routes_gated_by_env(monkeypatch):
    pytest.importorskip("fastapi")

    monkeypatch.setenv("DEBUG_ENDPOINTS", "false")
    import app.main as main_module

    main_module = importlib.reload(main_module)
    debug_paths_disabled = [route.path for route in main_module.app.routes if route.path.startswith("/debug")]
    assert debug_paths_disabled == []

    monkeypatch.setenv("DEBUG_ENDPOINTS", "true")
    main_module = importlib.reload(main_module)
    debug_paths_enabled = [route.path for route in main_module.app.routes if route.path.startswith("/debug")]
    assert len(debug_paths_enabled) > 0


def test_db_constraint_verification():
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='skill_progress'")
    skill_progress_ddl = cursor.fetchone()[0] or ""

    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='session_hash_registry'")
    hash_registry_ddl = cursor.fetchone()[0] or ""

    conn.close()

    assert "CHECK (NOT (is_unlocked = 1 AND unlocked_at IS NULL))" in skill_progress_ddl
    assert "CHECK (NOT (is_unlocked = 0 AND unlocked_at IS NOT NULL))" in skill_progress_ddl
    assert "session_hash TEXT PRIMARY KEY" in hash_registry_ddl


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
