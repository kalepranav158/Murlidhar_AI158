from fastapi import APIRouter, Query
from app.services.analytics_services import build_ml_forecast, build_skill_evolution,build_latest_radar
from database.db import  get_sessions
import statistics
from app.services.dashboard_service import build_dashboard
from app.future_plans.test_dashboard import analytics_dashboard
from app.services.analytics_services import build_risk_profile
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary(user_id: str):

    sessions = get_sessions(user_id=user_id, limit=100)

    if not sessions:
        return {"message": "No sessions available."}

    total = len(sessions)

    avg_note = statistics.mean(s["note_accuracy"] for s in sessions)
    avg_pitch = statistics.mean(s["avg_pitch_error"] for s in sessions)
    avg_time = statistics.mean(s["avg_timing_error"] for s in sessions)

    best = max(s["note_accuracy"] for s in sessions)
    worst = min(s["note_accuracy"] for s in sessions)

    return {
        "total_sessions": total,
        "average_note_accuracy": round(avg_note, 2),
        "average_pitch_error": round(avg_pitch, 2),
        "average_timing_error": round(avg_time, 2),
        "best_note_accuracy": best,
        "worst_note_accuracy": worst
    }

@router.get("/trend")
def get_trend(user_id: str):

    sessions = get_sessions(user_id=user_id, limit=50)

    if len(sessions) < 2:
        return {"message": "Not enough sessions."}

    sessions.reverse()

    return {
        "accuracy_series": [
            {
                "session": i + 1,
                "accuracy": s["note_accuracy"]
            }
            for i, s in enumerate(sessions)
        ]
    }


@router.get("/skill-level")
def get_skill_level(user_id: str):

    sessions = get_sessions(user_id=user_id, limit=50)

    if not sessions:
        return {"message": "No sessions available."}

    avg_note = sum(s["note_accuracy"] for s in sessions) / len(sessions)
    avg_pitch = sum(s["avg_pitch_error"] for s in sessions) / len(sessions)
    avg_time = sum(s["avg_timing_error"] for s in sessions) / len(sessions)

    # Classification logic
    if avg_note < 50:
        level = "Beginner"
    elif avg_note < 70:
        level = "Early Intermediate"
    elif avg_note < 85:
        level = "Intermediate"
    elif avg_note < 95:
        level = "Advanced"
    else:
        level = "Performance Ready"

    return {
        "skill_level": level,
        "average_note_accuracy": round(avg_note, 2),
        "average_pitch_error": round(avg_pitch, 2),
        "average_timing_error": round(avg_time, 2)
    }


@router.get("/consistency")
def get_consistency(user_id: str):

    sessions = get_sessions(user_id=user_id, limit=50)

    if len(sessions) < 3:
        return {"message": "Not enough sessions for consistency analysis."}

    accuracies = [s["note_accuracy"] for s in sessions]

    std_dev = statistics.stdev(accuracies)

    if std_dev < 5:
        consistency = "Highly Consistent"
    elif std_dev < 12:
        consistency = "Moderately Consistent"
    else:
        consistency = "Unstable Performance"

    return {
        "accuracy_standard_deviation": round(std_dev, 2),
        "consistency_level": consistency
    }


@router.get("/pitch-stability-control")
def get_pitch_stability(user_id: str):
    import statistics
    sessions = get_sessions(user_id=user_id, limit=50)

    if not sessions:
        return {"message": "No sessions available."}

    avg_pitch = sum(s["avg_pitch_error"] for s in sessions) / len(sessions)

    if avg_pitch < 10:
        level = "Excellent Control"
    elif avg_pitch < 25:
        level = "Good Control"
    elif avg_pitch < 40:
        level = "Needs Improvement"
    else:
        level = "Poor Pitch Stability"

    
    pitch_errors = [s["avg_pitch_error"] for s in sessions]

    mean_pitch = statistics.mean(pitch_errors)

    if len(pitch_errors) > 1:
        pitch_variation = statistics.stdev(pitch_errors)
    else:
        pitch_variation = 0.0

    # Control classification logic
    if mean_pitch < 10 and pitch_variation < 5:
        level = "Excellent Pitch Mastery"
    elif mean_pitch < 20:
        level = "Good Pitch Control"
    elif mean_pitch < 35:
        level = "Developing Control"
    else:
        level = "Unstable Pitch Foundation"

    return {
        "average_pitch_error": round(avg_pitch, 2),
        "mean_pitch_error": round(mean_pitch, 2),
        "pitch_variation": round(pitch_variation, 2),
        "pitch_control_level": level
    }

#-----------------------------------------
# Adaptive Practice Recommendation
#-----------------------------------------
@router.get("/recommendation-adaptive_plan")
def get_recommendation(user_id:str):
    import statistics
    sessions = get_sessions(user_id=user_id,limit=30)

    if not sessions:
        return {"message": "No sessions available."}

    avg_note = sum(s["note_accuracy"] for s in sessions) / len(sessions)
    avg_pitch = sum(s["avg_pitch_error"] for s in sessions) / len(sessions)

    if avg_note > 90 and avg_pitch < 15:
        suggestion = "Increase tempo by +10 BPM or try complex alankars."
    elif avg_note > 75:
        suggestion = "Maintain tempo. Focus on timing refinement."
    else:
        suggestion = "Practice slowly. Focus on clean note transitions."

    avg_note = statistics.mean(s["note_accuracy"] for s in sessions)
    avg_pitch = statistics.mean(s["avg_pitch_error"] for s in sessions)
    pitch_var = statistics.stdev(s["avg_pitch_error"] for s in sessions) if len(sessions) > 1 else 0

    # Decision logic
    if avg_note > 90 and avg_pitch < 15:
        tempo = "+10 BPM"
        focus = "Advanced alankars and speed control"
    elif avg_pitch > 30:
        tempo = "-10 BPM"
        focus = "Embouchure stability and airflow control"
    elif pitch_var > 15:
        tempo = "Maintain tempo"
        focus = "Consistency drills"
    else:
        tempo = "Maintain current tempo"
        focus = "Timing refinement"

    return {
        
        "recommended_tempo_adjustment": tempo,
        "practice_focus": focus,
        "suggestion": suggestion
    
    }


@router.get("/consistency-details")
def get_consistency_details(user_id: str):

    sessions = get_sessions(user_id=user_id, limit=50)

    if len(sessions) < 3:
        return {"message": "Not enough sessions."}

    accuracies = [s["note_accuracy"] for s in sessions]
    pitch_errors = [s["avg_pitch_error"] for s in sessions]
    timing_errors = [s["avg_timing_error"] for s in sessions]

    import statistics

    acc_std = statistics.stdev(accuracies)
    pitch_std = statistics.stdev(pitch_errors)
    time_std = statistics.stdev(timing_errors)

    main_issue = max(
        [("pitch", pitch_std), ("timing", time_std)],
        key=lambda x: x[1]
    )[0]

    return {
        "accuracy_variation": round(acc_std, 2),
        "pitch_variation": round(pitch_std, 2),
        "timing_variation": round(time_std, 2),
        "primary_instability_source": main_issue
    }    

@router.get("/dashboard")
def get_dashboard(user_id: str):
    return build_dashboard(user_id)


@router.get("/test-dashboard")
def test_dashboard(user_id: str):
    return analytics_dashboard(user_id=user_id)


@router.get("/analytics/radar")
def radar(user_id: str = Query(...)):

    try:
        return build_latest_radar(user_id)
    except Exception as e:
        return {"message": "Error generating radar data", "error": str(e)}

@router.get("/skill-evolution")
def skill_evolution(user_id: str):
    data = build_skill_evolution(user_id)
    if not data:
        return {"message": "No data found"}
    return data

@router.get("/risk")
def risk(user_id: str):

    try:
        return build_risk_profile(user_id)
    except Exception as e:
        return {"message": "Error generating risk profile", "error": str(e)}
    


@router.get("/forecast")
def forecast(user_id: str):

    
    try:
        return build_ml_forecast(user_id)
    except Exception as e:
        return {"message": "Error generating forecast", "error": str(e)}
