import statistics
import numpy as np
from database.db import get_sessions

def compute_analytics(user_id: str, limit: int = 50):

    sessions = get_sessions(user_id=user_id, limit=limit)

    if not sessions or len(sessions) < 3:
        return None

    sessions = list(reversed(sessions))

    accuracies = [s["note_accuracy"] for s in sessions]
    pitch_errors = [s["avg_pitch_error"] for s in sessions]
    timing_errors = [s["avg_timing_error"] for s in sessions]

    # -----------------------------
    # Regression
    # -----------------------------
    x = np.arange(len(accuracies))
    slope, intercept = np.polyfit(x, accuracies, 1)

    predicted_next = slope * len(accuracies) + intercept
    predicted_next = max(0, min(100, predicted_next))

    # -----------------------------
    # Averages
    # -----------------------------
    avg_accuracy = statistics.mean(accuracies)
    avg_pitch = statistics.mean(pitch_errors)
    avg_timing = statistics.mean(timing_errors)

    acc_std = statistics.stdev(accuracies)

    # -----------------------------
    # Indices
    # -----------------------------
    pitch_index = max(0, 1 - (avg_pitch / 50))
    rhythm_index = max(0, 1 - (avg_timing / 1))
    consistency_index = max(0, 1 - (acc_std / 30))

    composite_score = (
        0.4 * (avg_accuracy / 100)
        + 0.2 * pitch_index
        + 0.2 * rhythm_index
        + 0.2 * consistency_index
    )

    # -----------------------------
    # Classification
    # -----------------------------
    if slope > 0.5:
        trend_label = "Strong Improvement"
    elif slope > 0:
        trend_label = "Gradual Improvement"
    elif slope < -0.5:
        trend_label = "Declining"
    else:
        trend_label = "Plateau"

    plateau_flag = abs(slope) < 0.2 and acc_std < 5
    risk_flag = avg_pitch > 35 or avg_timing > 0.8

    return {
        "summary": {
            "average_accuracy": round(avg_accuracy, 2),
            "average_pitch_error": round(avg_pitch, 2),
            "average_timing_error": round(avg_timing, 2),
            "best_accuracy": max(accuracies),
            "worst_accuracy": min(accuracies),
        },
        "trend": {
            "slope": round(float(slope), 3),
            "classification": trend_label,
        },
        "indices": {
            "pitch_index": round(pitch_index, 3),
            "rhythm_index": round(rhythm_index, 3),
            "consistency_index": round(consistency_index, 3),
            "composite_score": round(composite_score, 3),
        },
        "prediction": {
            "next_accuracy": round(float(predicted_next), 2)
        },
        "flags": {
              "plateau": bool(plateau_flag),
               "risk": bool(risk_flag),
}

    }
