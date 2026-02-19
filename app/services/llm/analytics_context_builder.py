from database.db import get_sessions
import statistics
import numpy as np


def build_analytics_context(user_id: str):

    sessions = get_sessions(user_id=user_id, limit=50)

    if not sessions or len(sessions) < 3:
        return ""

    # Oldest first
    sessions = list(reversed(sessions))

    accuracies = [s["note_accuracy"] for s in sessions]
    pitch_errors = [s["avg_pitch_error"] for s in sessions]
    timing_errors = [s["avg_timing_error"] for s in sessions]

    # ----------------------------------
    # 1️⃣ Linear Trend (Regression)
    # ----------------------------------

    x = np.arange(len(accuracies))
    slope = np.polyfit(x, accuracies, 1)[0]
    last_accuracy = accuracies[-1]
    predicted_next_accuracy = last_accuracy + slope
    predicted_next_accuracy = max(0, min(100, predicted_next_accuracy))


    # ----------------------------------
    # 2️⃣ Averages
    # ----------------------------------

    avg_accuracy = statistics.mean(accuracies)
    avg_pitch = statistics.mean(pitch_errors)
    avg_timing = statistics.mean(timing_errors)

    # ----------------------------------
    # 3️⃣ Consistency
    # ----------------------------------

    acc_std = statistics.stdev(accuracies)

    # ----------------------------------
    # 4️⃣ Trend Classification
    # ----------------------------------

    if slope > 0.5:
        trend_label = "Strong Improvement"
    elif slope > 0:
        trend_label = "Gradual Improvement"
    elif slope < -0.5:
        trend_label = "Performance Declining"
    else:
        trend_label = "Plateau"

    # ----------------------------------
    # 5️⃣ Normalized Skill Indices (0–1)
    # ----------------------------------

    pitch_stability_index = max(0, 1 - (avg_pitch / 50))
    rhythm_stability_index = max(0, 1 - (avg_timing / 1))
    consistency_index = max(0, 1 - (acc_std / 30))
    breath_control_index = pitch_stability_index  # proxy for now

    composite_score = (
        0.35 * (avg_accuracy / 100)
        + 0.2 * pitch_stability_index
        + 0.2 * rhythm_stability_index
        + 0.15 * consistency_index
        + 0.1 * breath_control_index
    )

    # ----------------------------------
    # 6️⃣ Plateau + Risk Detection
    # ----------------------------------

    plateau_flag = abs(slope) < 0.2 and acc_std < 5
    risk_flag = avg_pitch > 35 or avg_timing > 0.8

    # ----------------------------------
    # Final Structured Context for LLM
    # ----------------------------------

    return f"""
Analytics Summary:
Average Accuracy: {round(avg_accuracy, 2)}%
Average Pitch Error: {round(avg_pitch, 2)} cents
Average Timing Error: {round(avg_timing, 2)} sec
Accuracy Consistency (Std Dev): {round(acc_std, 2)}

Learning Intelligence:
Trend Slope: {round(slope, 3)}
Trend Classification: {trend_label}
Composite Skill Score: {round(composite_score, 3)}

Skill Indices (0–1 Scale):
Pitch Stability Index: {round(pitch_stability_index, 3)}
Rhythm Stability Index: {round(rhythm_stability_index, 3)}
Consistency Index: {round(consistency_index, 3)}
Breath Control Index: {round(breath_control_index, 3)}

Alerts:
Plateau Detected: {plateau_flag}
Performance Risk Detected: {risk_flag}

Predicted Next Accuracy: {round(predicted_next_accuracy, 2)}%
"""
