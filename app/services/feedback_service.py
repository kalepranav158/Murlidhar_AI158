def generate_feedback(evaluation):
    feedback = []

    if evaluation["note_accuracy"] < 70:
        feedback.append("Focus on correct note transitions.")
    else:
        feedback.append("Good note accuracy.")

    if evaluation["avg_pitch_error_cents"] > 30:
        feedback.append("Pitch variation is high. Work on embouchure consistency.")
    else:
        feedback.append("Pitch control is stable.")

    if evaluation["avg_timing_error_sec"] > 0.5:
        feedback.append("Rhythmic stability needs improvement. Slow down and hold notes evenly.")
    else:
        feedback.append("Timing is well maintained.")

    return " ".join(feedback)
