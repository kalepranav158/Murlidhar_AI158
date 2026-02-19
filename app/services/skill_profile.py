# app/services/analytics/skill_profile_service.py
from database.db import get_sessions
import statistics
from typing import Dict, List


MAX_PITCH_ERROR = 50.0       # cents (beyond this = unstable)
MAX_TIMING_ERROR = 1.0       # seconds
MAX_STD_DEV = 20.0           # for consistency normalization
MAX_PITCH_STD = 40.0         # breath proxy normalization


def _safe_mean(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _safe_std(values: List[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def _normalize_inverse(value: float, max_value: float) -> float:
    """
    Converts error metric into 0–1 performance index.
    Lower error → Higher index.
    """
    if max_value == 0:
        return 0.0
    ratio = min(value / max_value, 1.0)
    return round(1.0 - ratio, 3)


def _normalize_direct(value: float, max_value: float) -> float:
    """
    Converts direct metric (like accuracy) into 0–1.
    """
    if max_value == 0:
        return 0.0
    return round(min(value / max_value, 1.0), 3)


def _compute_growth_rate(accuracies: List[float]) -> float:
    if len(accuracies) < 2:
        return 0.0

    first = accuracies[0]
    last = accuracies[-1]
    growth = (last - first) / len(accuracies)

    return round(growth, 3)


def build_skill_profile(user_id: str) -> Dict:
    """
    Computes longitudinal skill intelligence profile.
    """

    sessions = get_sessions(user_id=user_id, limit=50)

    if not sessions:
        return {
            "message": "No sessions available for skill profiling."
        }

    # Ensure chronological order (oldest → newest)
    sessions.reverse()

    accuracies = [s["note_accuracy"] for s in sessions]
    pitch_errors = [s["avg_pitch_error"] for s in sessions]
    timing_errors = [s["avg_timing_error"] for s in sessions]

    # -------------------------------
    # Core Metrics
    # -------------------------------

    avg_accuracy = _safe_mean(accuracies)
    avg_pitch_error = _safe_mean(pitch_errors)
    avg_timing_error = _safe_mean(timing_errors)

    pitch_std = _safe_std(pitch_errors)
    accuracy_std = _safe_std(accuracies)

    # -------------------------------
    # Skill Indices (0–1)
    # -------------------------------

    pitch_stability_index = _normalize_inverse(avg_pitch_error, MAX_PITCH_ERROR)
    rhythm_stability_index = _normalize_inverse(avg_timing_error, MAX_TIMING_ERROR)
    accuracy_index = _normalize_direct(avg_accuracy, 100.0)
    consistency_index = _normalize_inverse(accuracy_std, MAX_STD_DEV)
    breath_control_index = _normalize_inverse(pitch_std, MAX_PITCH_STD)

    # -------------------------------
    # Growth & Flags
    # -------------------------------

    growth_rate = _compute_growth_rate(accuracies)

    plateau_flag = (
        abs(growth_rate) < 0.2 and consistency_index > 0.7
    )

    risk_flag = (
        pitch_stability_index < 0.5 or rhythm_stability_index < 0.5
    )

    # -------------------------------
    # Composite Score (Optional)
    # -------------------------------

    composite_score = round(
        (
            pitch_stability_index +
            rhythm_stability_index +
            accuracy_index +
            consistency_index +
            breath_control_index
        ) / 5.0,
        3
    )

    return {
        "pitch_stability_index": pitch_stability_index,
        "rhythm_stability_index": rhythm_stability_index,
        "accuracy_index": accuracy_index,
        "breath_control_index": breath_control_index,
        "consistency_index": consistency_index,
        "growth_rate": growth_rate,
        "plateau_flag": plateau_flag,
        "risk_flag": risk_flag,
        "composite_score": composite_score,
        "total_sessions_analyzed": len(sessions)
    }
