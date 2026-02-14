from database.db import get_sessions
import statistics
import numpy as np


def build_analytics_context(user_id: str):

    sessions = get_sessions(user_id=user_id, limit=50)

    if not sessions or len(sessions) < 3:
        return ""

    # Reverse so oldest first
    sessions = list(reversed(sessions))

    accuracies = [s["note_accuracy"] for s in sessions]
    pitch_errors = [s["avg_pitch_error"] for s in sessions]
    timing_errors = [s["avg_timing_error"] for s in sessions]

    # ---- Trend (Linear Regression Slope) ----
    x = np.arange(len(accuracies))
    slope = np.polyfit(x, accuracies, 1)[0]

    # ---- Averages ----
    avg_accuracy = statistics.mean(accuracies)
    avg_pitch = statistics.mean(pitch_errors)
    avg_timing = statistics.mean(timing_errors)

    # ---- Consistency ----
    acc_std = statistics.stdev(accuracies)

    if slope > 0.5:
        trend_label = "Strong Improvement"
    elif slope > 0:
        trend_label = "Gradual Improvement"
    elif slope < -0.5:
        trend_label = "Performance Declining"
    else:
        trend_label = "Plateau"

    return f"""
Analytics Summary:
Average Accuracy: {round(avg_accuracy, 2)}%
Average Pitch Error: {round(avg_pitch, 2)} cents
Average Timing Error: {round(avg_timing, 2)} sec
Accuracy Consistency (Std Dev): {round(acc_std, 2)}
Learning Trend Slope: {round(slope, 3)}
Trend Classification: {trend_label}
"""
