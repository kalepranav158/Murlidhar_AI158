import statistics
import numpy as np
from database.db import get_sessions


def get_user_sessions(user_id: str, limit: int = 100):
    return get_sessions(user_id=user_id, limit=limit)


# ----------------------------------------
# Time Series Builder
# ----------------------------------------

def build_accuracy_series(user_id: str, limit: int = 50):
    sessions = get_user_sessions(user_id, limit)

    if not sessions:
        return []

    sessions.reverse()

    return [
        {"x": i + 1, "accuracy": s["note_accuracy"]}
        for i, s in enumerate(sessions)
    ]


# ----------------------------------------
# Regression Prediction
# ----------------------------------------

def build_prediction(user_id: str, limit: int = 50):

    sessions = get_user_sessions(user_id, limit)

    if len(sessions) < 3:
        return None

    sessions.reverse()

    y = np.array([s["note_accuracy"] for s in sessions])
    x = np.arange(len(y))

    # Linear regression
    slope, intercept = np.polyfit(x, y, 1)

    next_x = len(y)
    predicted = slope * next_x + intercept

    # Residual std deviation (confidence band)
    y_pred = slope * x + intercept
    residuals = y - y_pred
    std_dev = np.std(residuals)

    return {
        "predicted_next_accuracy": round(float(predicted), 2),
        "confidence_range": {
            "lower": round(float(predicted - std_dev), 2),
            "upper": round(float(predicted + std_dev), 2),
        }
    }


# ----------------------------------------
# Stability Metrics
# ----------------------------------------

def build_variation_metrics(user_id: str, limit: int = 50):

    sessions = get_user_sessions(user_id, limit)

    if len(sessions) < 3:
        return None

    accuracies = [s["note_accuracy"] for s in sessions]
    pitch = [s["avg_pitch_error"] for s in sessions]
    timing = [s["avg_timing_error"] for s in sessions]

    return {
        "accuracy_std": round(statistics.stdev(accuracies), 2),
        "pitch_std": round(statistics.stdev(pitch), 2),
        "timing_std": round(statistics.stdev(timing), 2),
    }


# ----------------------------------------
# KPI Summary
# ----------------------------------------

def build_summary(user_id: str, limit: int = 100):

    sessions = get_user_sessions(user_id, limit)

    if not sessions:
        return None

    avg_note = statistics.mean(s["note_accuracy"] for s in sessions)
    avg_pitch = statistics.mean(s["avg_pitch_error"] for s in sessions)

    return {
        "total_sessions": len(sessions),
        "avg_accuracy": round(avg_note, 2),
        "avg_pitch_error": round(avg_pitch, 2),
        "best_accuracy": max(s["note_accuracy"] for s in sessions),
    }
