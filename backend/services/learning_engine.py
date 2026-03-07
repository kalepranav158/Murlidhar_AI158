import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from backend.services.skill_profile import build_skill_profile
from backend.models.db import get_sessions

logger = logging.getLogger(__name__)

_FEATURE_NAMES = [
    "avg_pitch_error",
    "avg_timing_error",
    "pitch_index",
    "rhythm_index",
    "consistency_index",
    "composite_score",
    "technique_score",
]

_DEFAULT_WEIGHTS = [45.0, -0.40, -12.0, 18.0, 16.0, 10.0, 20.0, 8.0]

_MODEL_ARTIFACT_PATH = Path(__file__).resolve().parent.parent / "config" / "learning_model_artifact.json"
_MODEL_CACHE: dict[str, Any] | None = None
_MODEL_SOURCE = "uninitialized"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _default_artifact(reason: str) -> dict[str, Any]:
    return {
        "version": "1.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "feature_names": _FEATURE_NAMES,
        "weights": _DEFAULT_WEIGHTS,
        "metrics": {
            "sample_pairs": 0,
            "mae": None,
            "reason": reason,
        },
    }


def _session_feature_vector(session: dict[str, Any]) -> list[float]:
    return [
        _safe_float(session.get("avg_pitch_error")),
        _safe_float(session.get("avg_timing_error")),
        _safe_float(session.get("pitch_index")),
        _safe_float(session.get("rhythm_index")),
        _safe_float(session.get("consistency_index")),
        _safe_float(session.get("composite_score")),
        _safe_float(session.get("technique_score")),
    ]


def train_learning_model_from_history(limit: int = 600, minimum_pairs: int = 8) -> dict[str, Any]:
    sessions = get_sessions(user_id="", limit=limit)
    if len(sessions) < minimum_pairs + 1:
        return _default_artifact("not_enough_sessions")

    sessions = list(reversed(sessions))
    x_rows: list[list[float]] = []
    y_values: list[float] = []

    for index in range(len(sessions) - 1):
        current_session = sessions[index]
        next_session = sessions[index + 1]

        target_accuracy = next_session.get("note_accuracy")
        if target_accuracy is None:
            continue

        x_rows.append([1.0, *_session_feature_vector(current_session)])
        y_values.append(_safe_float(target_accuracy))

    if len(y_values) < minimum_pairs:
        return _default_artifact("not_enough_training_pairs")

    try:
        matrix = np.array(x_rows, dtype=float)
        labels = np.array(y_values, dtype=float)

        solved_weights = np.linalg.lstsq(matrix, labels, rcond=None)[0]
        predictions = matrix @ solved_weights
        mae = float(np.mean(np.abs(labels - predictions))) if len(labels) else None

        return {
            "version": "1.0",
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "feature_names": _FEATURE_NAMES,
            "weights": [round(float(weight), 6) for weight in solved_weights.tolist()],
            "metrics": {
                "sample_pairs": len(y_values),
                "mae": round(mae, 4) if mae is not None else None,
                "reason": "trained_from_sessions",
            },
        }
    except Exception:
        logger.exception("Learning model training failed, falling back to default weights")
        return _default_artifact("training_failure")


def save_model_artifact(artifact: dict[str, Any], artifact_path: str | Path | None = None) -> str:
    destination = Path(artifact_path) if artifact_path else _MODEL_ARTIFACT_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8") as handle:
        json.dump(artifact, handle, indent=2)

    return str(destination)


def load_model_artifact(artifact_path: str | Path | None = None) -> dict[str, Any] | None:
    source = Path(artifact_path) if artifact_path else _MODEL_ARTIFACT_PATH
    if not source.exists():
        return None

    try:
        with source.open("r", encoding="utf-8") as handle:
            artifact = json.load(handle)
    except Exception:
        logger.exception("Failed to read learning model artifact from %s", source)
        return None

    weights = artifact.get("weights")
    if not isinstance(weights, list) or len(weights) != len(_DEFAULT_WEIGHTS):
        logger.warning("Invalid learning model artifact weights in %s", source)
        return None

    return artifact


def train_and_persist_learning_model(
    limit: int = 600,
    minimum_pairs: int = 8,
    artifact_path: str | Path | None = None,
) -> dict[str, Any]:
    artifact = train_learning_model_from_history(limit=limit, minimum_pairs=minimum_pairs)
    save_model_artifact(artifact, artifact_path=artifact_path)
    return artifact


def initialize_learning_model() -> dict[str, Any]:
    global _MODEL_CACHE, _MODEL_SOURCE

    loaded = load_model_artifact()
    if loaded is not None:
        _MODEL_CACHE = loaded
        _MODEL_SOURCE = "artifact"
        return loaded

    trained = train_and_persist_learning_model()
    _MODEL_CACHE = trained
    sample_pairs = int((trained.get("metrics") or {}).get("sample_pairs") or 0)
    _MODEL_SOURCE = "trained" if sample_pairs > 0 else "fallback"
    return trained


def get_learning_model(force_reload: bool = False) -> dict[str, Any]:
    global _MODEL_CACHE

    if force_reload or _MODEL_CACHE is None:
        _MODEL_CACHE = initialize_learning_model()

    return _MODEL_CACHE


def get_learning_model_status() -> dict[str, Any]:
    model = get_learning_model()
    metrics = model.get("metrics") if isinstance(model, dict) else {}

    return {
        "loaded": isinstance(model, dict),
        "source": _MODEL_SOURCE,
        "artifact_path": str(_MODEL_ARTIFACT_PATH),
        "trained_at": model.get("trained_at") if isinstance(model, dict) else None,
        "sample_pairs": (metrics or {}).get("sample_pairs"),
        "mae": (metrics or {}).get("mae"),
        "reason": (metrics or {}).get("reason"),
    }


def predict_next_accuracy(session: dict[str, Any], model: dict[str, Any] | None = None) -> float:
    effective_model = model or get_learning_model()
    raw_weights = effective_model.get("weights") if isinstance(effective_model, dict) else None

    if not isinstance(raw_weights, list) or len(raw_weights) != len(_DEFAULT_WEIGHTS):
        raw_weights = _DEFAULT_WEIGHTS

    vector = np.array([1.0, *_session_feature_vector(session)], dtype=float)
    weights = np.array([_safe_float(weight) for weight in raw_weights], dtype=float)

    predicted = float(vector @ weights)
    return round(max(0.0, min(100.0, predicted)), 2)


def estimate_learning_difficulty(user_id: str) -> dict[str, Any] | None:
    sessions = get_sessions(user_id=user_id, limit=50)
    profile = build_skill_profile(user_id)

    if not sessions or "message" in profile:
        return None

    dimension_scores = {
        "pitch": _safe_float(profile.get("pitch_stability_index")),
        "rhythm": _safe_float(profile.get("rhythm_stability_index")),
        "consistency": _safe_float(profile.get("consistency_index")),
        "breath": _safe_float(profile.get("breath_control_index")),
    }
    weakest_dimension = min(dimension_scores, key=lambda key: dimension_scores[key])

    composite_score = _safe_float(profile.get("composite_score"))
    if composite_score >= 0.85:
        difficulty_level = "advanced"
        recommended_content_type = "song"
    elif composite_score >= 0.70:
        difficulty_level = "intermediate"
        recommended_content_type = "melody"
    else:
        difficulty_level = "foundation"
        recommended_content_type = "alankar"

    session_count = int(profile.get("total_sessions_analyzed") or len(sessions))
    confidence = "high" if session_count >= 20 else "medium" if session_count >= 8 else "low"

    return {
        "difficulty_level": difficulty_level,
        "recommended_content_type": recommended_content_type,
        "weakest_dimension": weakest_dimension,
        "composite_score": round(composite_score, 3),
        "confidence": confidence,
        "total_sessions_analyzed": session_count,
    }


def generate_learning_recommendation(user_id: str) -> dict[str, Any] | None:
    sessions = get_sessions(user_id=user_id, limit=50)
    if not sessions:
        return None

    difficulty = estimate_learning_difficulty(user_id)
    if difficulty is None:
        return None

    latest_session = sessions[0]
    predicted_next_accuracy = predict_next_accuracy(latest_session)

    difficulty_level = difficulty.get("difficulty_level")
    weakest_dimension = difficulty.get("weakest_dimension")

    if difficulty_level == "foundation":
        tempo_adjustment = "-10 BPM"
        practice_focus = f"{weakest_dimension} stabilization drills"
        recommendation = "Slow down and prioritize clean transitions and stability."
    elif difficulty_level == "intermediate":
        tempo_adjustment = "Maintain tempo"
        practice_focus = f"{weakest_dimension} refinement with melody phrasing"
        recommendation = "Maintain control and improve phrase consistency."
    else:
        tempo_adjustment = "+8 BPM"
        practice_focus = "musical phrasing and expressive control"
        recommendation = "Increase challenge with advanced phrase flow and tempo control."

    return {
        "predicted_next_accuracy": predicted_next_accuracy,
        "recommended_tempo_adjustment": tempo_adjustment,
        "practice_focus": practice_focus,
        "recommendation": recommendation,
        "recommended_content_type": difficulty.get("recommended_content_type"),
        "difficulty_level": difficulty_level,
        "model_source": _MODEL_SOURCE,
    }

