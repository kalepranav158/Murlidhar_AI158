import json
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import database.db as db
from app.services.learning_engine import (
    estimate_learning_difficulty,
    generate_learning_recommendation,
    predict_next_accuracy,
    train_learning_model_from_history,
)


@contextmanager
def _temporary_db_with_sessions(user_id: str = "ml_user", count: int = 12):
    original_db_name = db.DB_NAME
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir) / "learning_engine.db"
        db.init_db(str(temp_db_path))

        conn = sqlite3.connect(str(temp_db_path))
        cursor = conn.cursor()

        base_time = datetime.now(timezone.utc) - timedelta(days=count)
        for index in range(count):
            note_accuracy = 60 + index
            avg_pitch_error = max(4.0, 30.0 - (index * 1.1))
            avg_timing_error = max(0.08, 0.55 - (index * 0.025))
            pitch_index = max(0.0, 1 - (avg_pitch_error / 50.0))
            rhythm_index = max(0.0, 1 - avg_timing_error)
            consistency_index = min(1.0, 0.45 + (index * 0.03))
            technique_score = min(1.0, 0.2 + (index * 0.05))
            composite_score = min(
                1.0,
                (0.4 * (note_accuracy / 100.0)) + (0.3 * pitch_index) + (0.3 * rhythm_index),
            )

            cursor.execute(
                """
                INSERT INTO sessions (
                    user_id,
                    timestamp,
                    reference,
                    played_notes,
                    note_accuracy,
                    avg_pitch_error,
                    avg_timing_error,
                    mistakes,
                    composite_score,
                    pitch_index,
                    rhythm_index,
                    consistency_index,
                    technique_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    (base_time + timedelta(days=index)).isoformat(),
                    json.dumps([]),
                    json.dumps([]),
                    float(note_accuracy),
                    float(avg_pitch_error),
                    float(avg_timing_error),
                    json.dumps([]),
                    float(composite_score),
                    float(pitch_index),
                    float(rhythm_index),
                    float(consistency_index),
                    float(technique_score),
                ),
            )

        conn.commit()
        conn.close()

        try:
            yield user_id
        finally:
            db.DB_NAME = original_db_name


def test_learning_model_training_and_inference_shape():
    with _temporary_db_with_sessions() as user_id:
        model = train_learning_model_from_history(limit=200, minimum_pairs=5)

        assert isinstance(model, dict)
        assert isinstance(model.get("weights"), list)
        assert len(model["weights"]) == 8

        latest = db.get_sessions(user_id=user_id, limit=1)[0]
        prediction = predict_next_accuracy(latest, model=model)
        assert isinstance(prediction, float)
        assert 0.0 <= prediction <= 100.0


def test_learning_difficulty_and_recommendation_payloads():
    with _temporary_db_with_sessions() as user_id:
        difficulty = estimate_learning_difficulty(user_id)
        recommendation = generate_learning_recommendation(user_id)

        assert difficulty is not None
        assert recommendation is not None

        assert "difficulty_level" in difficulty
        assert "recommended_content_type" in difficulty
        assert "weakest_dimension" in difficulty

        assert "predicted_next_accuracy" in recommendation
        assert "practice_focus" in recommendation
        assert "recommended_tempo_adjustment" in recommendation
        assert "recommended_content_type" in recommendation
