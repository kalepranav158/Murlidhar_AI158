from fastapi import APIRouter
from database.db import get_sessions
import statistics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary():

    sessions = get_sessions(limit=100)

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
def get_trend():

    sessions = get_sessions(limit=50)

    if len(sessions) < 2:
        return {"message": "Not enough sessions for trend analysis."}

    sessions.reverse()  # oldest first

    first = sessions[0]["note_accuracy"]
    last = sessions[-1]["note_accuracy"]

    improvement = last - first

    direction = "improving" if improvement > 0 else "declining"

    return {
        "start_accuracy": first,
        "latest_accuracy": last,
        "change": round(improvement, 2),
        "trend": direction
    }


@router.get("/skill-level")
def get_skill_level():

    sessions = get_sessions(limit=50)

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
def get_consistency():

    sessions = get_sessions(limit=50)

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



@router.get("/pitch-stability")
def get_pitch_stability():

    sessions = get_sessions(limit=50)

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

    return {
        "average_pitch_error": round(avg_pitch, 2),
        "pitch_stability_level": level
    }


@router.get("/recommendation")
def get_recommendation():

    sessions = get_sessions(limit=30)

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

    return {
        "suggestion": suggestion
    }
 
@router.get("/consistency-details")
def get_consistency_details():

    sessions = get_sessions(limit=50)

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


@router.get("/pitch-control")
def get_pitch_control():

    sessions = get_sessions(limit=50)

    if not sessions:
        return {"message": "No sessions available."}

    import statistics

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
        "average_pitch_error": round(mean_pitch, 2),
        "pitch_variation": round(pitch_variation, 2),
        "pitch_control_level": level
    }


@router.get("/adaptive-plan")
def get_adaptive_plan():

    sessions = get_sessions(limit=50)

    if not sessions:
        return {"message": "No sessions available."}

    import statistics

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
        "practice_focus": focus
    }
