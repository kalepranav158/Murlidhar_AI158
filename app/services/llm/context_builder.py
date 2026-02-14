# app/services/context_builder.py

from database.db import get_last_session

def build_practice_context(user_id: str):
    last = get_last_session(user_id)

    if not last:
        return ""

    return f"""
    Last Practice Summary:
    Accuracy: {last['note_accuracy']}%
    Avg Pitch Error: {last['avg_pitch_error']}
    Avg Timing Error: {last['avg_timing_error']}
    """
