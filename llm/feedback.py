def generate_feedback(result, progress_stats=None):
    score = result["note_accuracy"]
    pitch = result["avg_pitch_error_cents"]
    timing = result["avg_timing_error_sec"]

    feedback = []

    # Note accuracy
    if score >= 90:
        feedback.append("Your note sequence is very accurate.")
    elif score >= 70:
        feedback.append("Your note order is mostly correct, but transitions need refinement.")
    else:
        feedback.append("Focus on correct note transitions. Practice slowly with clear articulation.")

    # Pitch quality
    if pitch is not None:
        if pitch < 10:
            feedback.append("Your intonation is stable and controlled.")
        elif pitch < 25:
            feedback.append("Pitch is slightly unstable. Focus on steady airflow.")
        else:
            feedback.append("Pitch variation is high. Work on embouchure consistency.")

    # Timing quality
    if timing is not None:
        if timing < 0.5:
            feedback.append("Your rhythm is steady.")
        elif timing < 1.5:
            feedback.append("Timing varies slightly. Practice with a slow metronome.")
        else:
            feedback.append("Rhythmic stability needs improvement. Slow down and hold notes evenly.")

    # Progress awareness
    if progress_stats and progress_stats["recent_improvement"] is not None:
        if progress_stats["recent_improvement"] > 0:
            feedback.append("You are improving compared to previous sessions. Keep practicing consistently.")
        else:
            feedback.append("Progress seems stable. Try focused repetition on weak transitions.")

    return " ".join(feedback)
