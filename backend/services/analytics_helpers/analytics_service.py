from backend.models.db import get_sessions
from .trend_analyzer import compute_trend
from .consistency_calculator import compute_consistency
from .performance_classifier import classify_performance


def generate_analytics(user_id: str):

    sessions = get_sessions(limit=50)

    if not sessions:
        return {"message": "No sessions available"}

    accuracies = [s["note_accuracy"] for s in sessions]
    pitch_errors = [s["avg_pitch_error"] for s in sessions]
    timing_errors = [s["avg_timing_error"] for s in sessions]

    accuracy_trend = compute_trend(accuracies)
    pitch_trend = compute_trend(pitch_errors)
    timing_trend = compute_trend(timing_errors)

    consistency_score = compute_consistency(accuracies)

    avg_accuracy = sum(accuracies) / len(accuracies)
    avg_pitch = sum(pitch_errors) / len(pitch_errors)
    avg_timing = sum(timing_errors) / len(timing_errors)

    level = classify_performance(avg_accuracy, avg_pitch, avg_timing)

    return {
        "average_accuracy": avg_accuracy,
        "accuracy_trend_slope": accuracy_trend,
        "pitch_error_trend_slope": pitch_trend,
        "timing_error_trend_slope": timing_trend,
        "consistency_score": consistency_score,
        "performance_level": level
    }

