import os
import json
import pytest
from database.db import init_db, DB_NAME, update_alankar_mastery
from app.services.curriculum_service import evaluate_curriculum_progress

USER = "test_user"


def setup_module(module):
    # ensure fresh database for tests
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()
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
    with open("songs/alankar_test.json", "w") as f:
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
    with open("songs/alankar_next.json", "w") as f:
        json.dump(content2, f)


def teardown_module(module):
    # clean up
    for fname in ["songs/alankar_test.json", "songs/alankar_next.json"]:
        try:
            os.remove(fname)
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
    # simulate mastering the test alankar
    update_alankar_mastery(USER, "alankar_test", level_index=1, tempo=60, composite_score=0.95)
    cur = evaluate_curriculum_progress(USER)
    assert "alankar_test" in cur["mastered_content"]
    assert "alankar_next" in cur["unlocked_content"]
    assert cur["recommended_content"] == "alankar_next"


def test_locked_list_filters_none():
    # create a content file without an id to simulate bad data
    bad_content = {"type": "song", "level": "beginner", "phrases": []}
    with open("songs/bad.json", "w") as f:
        json.dump(bad_content, f)

    cur = evaluate_curriculum_progress(USER)
    # locked list should not include None even though a file lacked an id
    assert None not in cur["locked"]
    # and locked should be a list of strings only
    assert all(isinstance(x, str) for x in cur["locked"])

    # cleanup
    try:
        os.remove("songs/bad.json")
    except OSError:
        pass


def test_snapshot_includes_technique():
    # insert two fake sessions with technique scores
    from database.db import save_session

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
