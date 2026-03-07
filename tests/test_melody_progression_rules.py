import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

import backend.models.db as db
from backend.services.curriculum_service import evaluate_curriculum_progress


@contextmanager
def _temporary_db():
    original_db_name = db.DB_NAME
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir) / "melody_progression.db"
        db.init_db(str(temp_db_path))
        try:
            yield
        finally:
            db.DB_NAME = original_db_name


def _seed_student(user_id: str, unlocked_content: list[str]):
    db.update_student_progress(
        user_id,
        {
            "user_id": user_id,
            "current_level": "beginner",
            "unlocked_content": unlocked_content,
            "mastered_content": [],
            "last_evaluated": None,
        },
    )


def _mark_phrase_mastered(user_id: str, melody_id: str, phrase_index: int):
    skill_id = f"{melody_id}:melody_phrase:{phrase_index}"
    for index in range(3):
        db.update_skill_progress(
            user_id=user_id,
            skill_id=skill_id,
            skill_type="melody_phrase",
            composite_score=0.96,
            threshold=0.90,
            session_hash=f"{user_id}:{skill_id}:{index}",
        )


def test_melody_unlock_requires_full_phrase_mastery():
    user_id = "melody_progress_user_partial"
    with _temporary_db():
        _seed_student(user_id, ["melody_1"])

        _mark_phrase_mastered(user_id, "melody_1", 0)

        curriculum = evaluate_curriculum_progress(user_id)

        assert "melody_1" not in curriculum.get("mastered_content", [])
        assert "melody_2" not in curriculum.get("unlocked_content", [])


def test_melody_unlocks_next_after_full_mastery():
    user_id = "melody_progress_user_full"
    with _temporary_db():
        _seed_student(user_id, ["melody_1"])

        melody_path = Path("data/songs/catalog") / "melody_1.json"
        with melody_path.open("r", encoding="utf-8") as handle:
            melody_payload = json.load(handle)

        phrase_count = len(melody_payload.get("phrases", []))
        for phrase_index in range(phrase_count):
            _mark_phrase_mastered(user_id, "melody_1", phrase_index)

        curriculum = evaluate_curriculum_progress(user_id)

        assert "melody_1" in curriculum.get("mastered_content", [])
        assert "melody_2" in curriculum.get("unlocked_content", [])


def test_curriculum_content_lists_are_sorted():
    user_id = "melody_progress_user_order"
    with _temporary_db():
        _seed_student(user_id, ["song_1", "alankar_1", "melody_1"])

        curriculum = evaluate_curriculum_progress(user_id)

        unlocked_content = curriculum.get("unlocked_content", [])
        mastered_content = curriculum.get("mastered_content", [])

        assert unlocked_content == sorted(unlocked_content)
        assert mastered_content == sorted(mastered_content)

