from fastapi import Query
from backend.models.db import get_sessions
import numpy as np
import statistics
from datetime import datetime



def analytics_dashboard(user_id: str = Query(...), limit: int = 50):

    sessions = get_sessions(user_id=user_id, limit=limit)

    if not sessions or len(sessions) < 3:
        return {
            "error": "Not enough sessions for analytics"
        }

    # Oldest first
    sessions.reverse()

    accuracies = [float(s["note_accuracy"]) for s in sessions]
    pitch_errors = [float(s["avg_pitch_error"]) for s in sessions]
    timing_errors = [float(s["avg_timing_error"]) for s in sessions]
    timestamps = [s["timestamp"] for s in sessions]

    # -----------------------------------
    # KPI
    # -----------------------------------

    avg_accuracy = round(statistics.mean(accuracies), 2)
    avg_pitch = round(statistics.mean(pitch_errors), 2)
    avg_timing = round(statistics.mean(timing_errors), 2)

    best_accuracy = float(max(accuracies))
    worst_accuracy = float(min(accuracies))

    # -----------------------------------
    # TREND ANALYSIS
    # -----------------------------------

    x = np.arange(len(accuracies))
    slope, intercept = np.polyfit(x, accuracies, 1)

    slope = float(round(slope, 3))

    if slope > 0.5:
        trend_class = "Strong Improvement"
    elif slope > 0:
        trend_class = "Gradual Improvement"
    elif slope < -0.5:
        trend_class = "Declining"
    else:
        trend_class = "Plateau"

    momentum_score = float(round(min(1, abs(slope) / 2), 3))

    # -----------------------------------
    # SKILL INDICES (0-1 normalized)
    # -----------------------------------

    pitch_index = float(round(max(0, 1 - (avg_pitch / 50)), 3))
    rhythm_index = float(round(max(0, 1 - (avg_timing / 1)), 3))

    acc_std = statistics.stdev(accuracies)
    consistency_index = float(round(max(0, 1 - (acc_std / 30)), 3))

    breath_control_index = pitch_index

    composite_score = float(round(
        0.35 * (avg_accuracy / 100)
        + 0.2 * pitch_index
        + 0.2 * rhythm_index
        + 0.15 * consistency_index
        + 0.1 * breath_control_index,
        3
    ))

    # -----------------------------------
    # FORECAST
    # -----------------------------------

    y_pred = slope * x + intercept
    residuals = np.array(accuracies) - y_pred
    residual_std = float(np.std(residuals))

    next_x = len(accuracies)
    next_prediction = float(round(
        max(0, min(100, slope * next_x + intercept)), 2
    ))

    next_5_projection = [
        float(round(max(0, min(100, slope * (next_x + i) + intercept)), 2))
        for i in range(1, 6)
    ]

    confidence_lower = float(round(next_prediction - residual_std, 2))
    confidence_upper = float(round(next_prediction + residual_std, 2))

    # -----------------------------------
    # RISK DETECTION
    # -----------------------------------

    plateau_flag = bool(abs(slope) < 0.2 and acc_std < 5)
    risk_flag = bool(avg_pitch > 35 or avg_timing > 0.8)

    if acc_std < 5:
        volatility = "Low"
    elif acc_std < 15:
        volatility = "Moderate"
    else:
        volatility = "High"

    # -----------------------------------
    # TRAINING RECOMMENDATION
    # -----------------------------------

    if composite_score > 0.8:
        difficulty = "Increase Tempo +10 BPM"
    elif composite_score < 0.5:
        difficulty = "Reduce Tempo -10 BPM"
    else:
        difficulty = "Maintain Current Tempo"

    if pitch_index < rhythm_index:
        focus_area = "Pitch Stability"
    elif rhythm_index < pitch_index:
        focus_area = "Rhythm Stability"
    else:
        focus_area = "Consistency"

    if pitch_index < 0.6:
        practice_type = "Long Note Swar Sadhana"
    elif rhythm_index < 0.6:
        practice_type = "Slow Metronome Alankars"
    else:
        practice_type = "Speed + Expression Control"

    # -----------------------------------
    # FINAL RESPONSE
    # -----------------------------------

    return {
        "meta": {
            "user_id": user_id,
            "total_sessions": len(sessions),
            "analysis_window": limit,
            "generated_at": datetime.utcnow().isoformat()
        },

        "kpi": {
            "average_accuracy": avg_accuracy,
            "average_pitch_error": avg_pitch,
            "average_timing_error": avg_timing,
            "best_accuracy": best_accuracy,
            "worst_accuracy": worst_accuracy
        },

        "trend_analysis": {
            "accuracy_slope": slope,
            "classification": trend_class,
            "momentum_score": momentum_score
        },

        "skill_indices": {
            "pitch_stability_index": pitch_index,
            "rhythm_stability_index": rhythm_index,
            "consistency_index": consistency_index,
            "breath_control_index": breath_control_index,
            "composite_skill_score": composite_score
        },

        "forecast": {
            "next_session_prediction": next_prediction,
            "next_5_projection": next_5_projection,
            "confidence_band": {
                "lower_bound": confidence_lower,
                "upper_bound": confidence_upper
            }
        },

        "risk_analysis": {
            "plateau_detected": plateau_flag,
            "performance_risk_detected": risk_flag,
            "volatility_level": volatility
        },

        "training_recommendation": {
            "difficulty_adjustment": difficulty,
            "focus_area": focus_area,
            "recommended_practice_type": practice_type
        },

        "visualization": {
            "time_series": {
                "timestamps": timestamps,
                "accuracy_curve": accuracies,
                "pitch_curve": pitch_errors,
                "timing_curve": timing_errors
            },
            "distributions": {
                "accuracy_std_dev": float(round(acc_std, 2)),
                "pitch_std_dev": float(round(statistics.stdev(pitch_errors), 2)),
                "timing_std_dev": float(round(statistics.stdev(timing_errors), 2))
            }
        }
    }
