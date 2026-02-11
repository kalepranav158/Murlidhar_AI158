from database.db import get_all_sessions


def compute_progress():
    sessions = get_all_sessions()

    if not sessions:
        return None

    scores = [s[4] for s in sessions]  # note_accuracy
    pitch_errors = [s[5] for s in sessions if s[5] is not None]
    timing_errors = [s[6] for s in sessions if s[6] is not None]

    avg_score = sum(scores) / len(scores)
    best_score = max(scores)

    improvement = None
    if len(scores) >= 2:
        improvement = scores[0] - scores[-1]

    return {
        "total_sessions": len(scores),
        "average_score": round(avg_score, 2),
        "best_score": best_score,
        "average_pitch_error": round(sum(pitch_errors)/len(pitch_errors), 2) if pitch_errors else None,
        "average_timing_error": round(sum(timing_errors)/len(timing_errors), 2) if timing_errors else None,
        "recent_improvement": round(improvement, 2) if improvement is not None else None
    }
