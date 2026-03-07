import os
import json
import pytest
import uuid
import backend.models.db as db
from backend.models.db import init_db, update_skill_progress
from backend.services.curriculum_service import evaluate_curriculum_progress

USER = "test_user"
TEST_DB = None


def _assert_not_live_db(path: str):
    live_name = "practice_data.db"
    if os.path.basename(path).lower() == live_name:
        raise RuntimeError(
            "Refusing to run tests against live Practice_data.db. "
            "Use an isolated test DB file."
        )


def setup_module(module):
    global TEST_DB
    TEST_DB = f"test_curriculum_{uuid.uuid4().hex}.db"
    _assert_not_live_db(TEST_DB)
    db.DB_NAME = TEST_DB
    init_db(TEST_DB)
    # create a simple alankar json for unlocking
    content = {
        "id": "alankar_test",
        "type": "alankar",
        "level": "beginner",
        "required_accuracy": 80,
        "required_rhythm_index": 0.6,
        "required_technique_score": 0.0,
        "unlock_next": "alankar_next",
        "phrases": []
    }
    with open("data/songs/catalog/alankar_test.json", "w") as f:
        json.dump(content, f)
    content2 = {
        "id": "alankar_next",
        "type": "alankar",
        "level": "beginner",
        "required_accuracy": 80,
        "required_rhythm_index": 0.6,
        "required_technique_score": 0.0,
        "unlock_next": None,
        "phrases": []
    }
    with open("data/songs/catalog/alankar_next.json", "w") as f:
        json.dump(content2, f)


def teardown_module(module):
    global TEST_DB
    # clean up
    for fname in ["data/songs/catalog/alankar_test.json", "data/songs/catalog/alankar_next.json"]:
        try:
            os.remove(fname)
        except OSError:
            pass
    if TEST_DB and os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass


def test_initial_profile_empty():
    cur = evaluate_curriculum_progress(USER)
    assert cur["current_level"] == "beginner"
    # initial evaluation should unlock available beginner content
    assert "alankar_test" in cur["unlocked_content"]
    assert cur["mastered_content"] == []
    # recommendation should point to first unlocked
    assert cur["recommended_content"] in cur["unlocked_content"]


def test_unlock_after_mastering():
    # canonical model unlocks after 3 successful sessions
    for _ in range(3):
        update_skill_progress(USER, "alankar_test", "alankar", 0.95, 0.75)
    cur = evaluate_curriculum_progress(USER)
    assert "alankar_test" in cur["mastered_content"]
    assert "alankar_next" in cur["unlocked_content"]
    assert cur["recommended_content"] == "alankar_next"


def test_locked_list_filters_none():
    # create a content file without an id to simulate bad data
    bad_content = {"type": "song", "level": "beginner", "phrases": []}
    with open("data/songs/catalog/bad.json", "w") as f:
        json.dump(bad_content, f)

    cur = evaluate_curriculum_progress(USER)
    # locked list should not include None even though a file lacked an id
    assert None not in cur["locked"]
    # and locked should be a list of strings only
    assert all(isinstance(x, str) for x in cur["locked"])

    # cleanup
    try:
        os.remove("data/songs/catalog/bad.json")
    except OSError:
        pass


def test_snapshot_includes_technique():
    # insert two fake sessions with technique scores
    from backend.models.db import save_session

    save_session(USER, [], [], {
        "note_accuracy": 90,
        "avg_pitch_error_cents": 5,
        "avg_timing_error_sec": 0.1,
        "mistakes": [],
        "composite_score": 0.9,
        "pitch_index": 0.8,
        "rhythm_index": 0.9,
        "consistency_index": 1.0,
        "technique_score": 0.7
    })
    save_session(USER, [], [], {
        "note_accuracy": 85,
        "avg_pitch_error_cents": 10,
        "avg_timing_error_sec": 0.2,
        "mistakes": [],
        "composite_score": 0.85,
        "pitch_index": 0.75,
        "rhythm_index": 0.8,
        "consistency_index": 1.0,
        "technique_score": 0.9
    })

    cur = evaluate_curriculum_progress(USER)
    # average of 0.7 and 0.9 should be 0.8
    assert abs(cur["skill_snapshot"]["technique_score"] - 0.8) < 0.001

