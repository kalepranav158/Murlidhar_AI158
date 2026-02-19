import statistics
import numpy as np
from database.db import get_sessions


def build_dashboard(user_id: str):

    sessions = get_sessions(user_id=user_id, limit=100)

    if not sessions or len(sessions) < 3:
        return {"message": "Not enough data for dashboard."}
    # remove outliers to prevent skewing the dashboard
    sessions = list(reversed(sessions))
    accuracies = remove_outliers([s["note_accuracy"] for s in sessions])


    # Oldest first
    pitch_errors = [s["avg_pitch_error"] for s in sessions]
    timing_errors = [s["avg_timing_error"] for s in sessions]
    timestamps = [s["timestamp"] for s in sessions]

    # ------------------------
    # Basic Metrics
    # ------------------------
    avg_accuracy = statistics.mean(accuracies)
    avg_pitch = statistics.mean(pitch_errors)
    avg_timing = statistics.mean(timing_errors)

    best_accuracy = max(accuracies)
    worst_accuracy = min(accuracies)

    # ------------------------
    # Trend (Linear Regression)
    # ------------------------
    x = np.arange(len(accuracies))
    slope = np.polyfit(x, accuracies, 1)[0]

    if slope > 0.5:
        trend_label = "Strong Improvement"
    elif slope > 0:
        trend_label = "Gradual Improvement"
    elif slope < -0.5:
        trend_label = "Performance Declining"
    else:
        trend_label = "Plateau"

    # ------------------------
    # Consistency
    # ------------------------
    std_dev = statistics.stdev(accuracies)

    if std_dev < 5:
        consistency = "Highly Consistent"
    elif std_dev < 12:
        consistency = "Moderately Consistent"
    else:
        consistency = "Unstable"

    # ------------------------
    # Prediction (Next 5 Sessions)
    # ------------------------
    next_points = []
    for i in range(1, 6):
        predicted = min(100, max(0, accuracies[-1] + slope * i))
        next_points.append(round(predicted, 2))

    # ------------------------
    # Difficulty Recommendation
    # ------------------------
    if avg_accuracy > 90 and avg_pitch < 15:
        difficulty = "Increase Tempo +10 BPM"
    elif avg_accuracy > 75:
        difficulty = "Maintain Tempo, Refine Timing"
    else:
        difficulty = "Reduce Tempo, Focus on Clean Notes"

    # ------------------------
    # Return Structured Dashboard
    # ------------------------
    return {
        "summary": {
            "average_accuracy": round(avg_accuracy, 2),
            "average_pitch_error": round(avg_pitch, 2),
            "average_timing_error": round(avg_timing, 2),
            "best_accuracy": best_accuracy,
            "worst_accuracy": worst_accuracy,
        },
        "trend": {
            "slope": round(slope, 3),
            "classification": trend_label,
        },
        "consistency": {
            "std_deviation": round(std_dev, 2),
            "level": consistency,
        },
        "prediction": {
            "next_5_accuracy_projection": next_points
        },
        "difficulty_recommendation": difficulty,
        "chart_data": {
            "timestamps": timestamps,
            "accuracy_curve": accuracies,
            "pitch_curve": pitch_errors,
            "timing_curve": timing_errors,
        }
    }

def remove_outliers(data):
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return [x for x in data if lower <= x <= upper]
