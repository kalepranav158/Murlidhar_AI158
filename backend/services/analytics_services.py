import statistics
import numpy as np
from backend.models.db import get_sessions
import numpy as np


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

def build_skill_evolution(user_id: str, limit: int = 100):

    sessions = get_sessions(user_id=user_id, limit=limit)

    if not sessions:
        return None

    sessions = list(reversed(sessions))  # oldest first

    return {
        "timestamps": [s["timestamp"] for s in sessions],
        "composite_curve": [s.get("composite_score") for s in sessions],
        "pitch_curve": [s.get("pitch_index") for s in sessions],
        "rhythm_curve": [s.get("rhythm_index") for s in sessions],
        "consistency_curve": [s.get("consistency_index") for s in sessions],
    }






def build_latest_radar(user_id: str):

    sessions = get_user_sessions(user_id=user_id, limit=1)

    if not sessions:
        return None

    latest = sessions[0]

    return {
        "pitch": latest.get("pitch_index") or 0,
        "rhythm": latest.get("rhythm_index") or 0,
        "consistency": latest.get("consistency_index") or 0,
        "composite": latest.get("composite_score") or 0,
    }





def build_risk_profile(user_id: str, limit: int = 50):

    sessions = get_user_sessions(user_id=user_id, limit=limit)

    if len(sessions) < 3:
        return None

    accuracies = [s["note_accuracy"] for s in sessions]
    pitch_errors = [s["avg_pitch_error"] for s in sessions]
    timing_errors = [s["avg_timing_error"] for s in sessions]

    avg_pitch = sum(pitch_errors) / len(pitch_errors)
    avg_timing = sum(timing_errors) / len(timing_errors)

    volatility = np.std(accuracies)

    # Normalize risks
    pitch_risk = min(1, avg_pitch / 50)
    timing_risk = min(1, avg_timing / 1)
    volatility_risk = min(1, volatility / 30)

    risk_score = (
        0.4 * pitch_risk +
        0.3 * timing_risk +
        0.3 * volatility_risk
    )

    if risk_score < 0.3:
        level = "Low"
    elif risk_score < 0.6:
        level = "Moderate"
    else:
        level = "High"

    return {
        "risk_score": round(risk_score, 3),
        "risk_level": level,
        "components": {
            "pitch_risk": round(pitch_risk, 3),
            "timing_risk": round(timing_risk, 3),
            "volatility_risk": round(volatility_risk, 3)
        }
    }





def build_ml_forecast(user_id: str, limit: int = 50):

    sessions = get_user_sessions(user_id=user_id, limit=limit)

    if len(sessions) < 5:
        return None

    # Oldest first
    sessions = list(reversed(sessions))

    # Build feature matrix
    X = []
    y = []

    for i in range(len(sessions) - 1):
        s = sessions[i]
        next_s = sessions[i + 1]

        X.append([
            s["avg_pitch_error"],
            s["avg_timing_error"],
            s["pitch_index"],
            s["rhythm_index"],
            s["consistency_index"],
            s["composite_score"]
        ])

        y.append(next_s["note_accuracy"])

    X = np.array(X)
    y = np.array(y)

    # Add bias column
    X = np.column_stack([np.ones(len(X)), X])

    # Linear regression weights
    try:
        weights = np.linalg.lstsq(X, y, rcond=None)[0]
    except Exception:
        return None

    # Predict next based on latest session
    latest = sessions[-1]

    latest_features = np.array([
        1,
        latest["avg_pitch_error"],
        latest["avg_timing_error"],
        latest["pitch_index"],
        latest["rhythm_index"],
        latest["consistency_index"],
        latest["composite_score"]
    ])

    predicted = float(np.dot(latest_features, weights))

    # Clamp to realistic bounds
    predicted = max(0, min(100, predicted))

    return {
        "predicted_next_accuracy": round(predicted, 2)
    }
