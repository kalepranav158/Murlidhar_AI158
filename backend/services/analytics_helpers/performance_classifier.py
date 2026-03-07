def classify_performance(avg_accuracy, avg_pitch_error, avg_timing_error):

    if avg_accuracy > 90 and avg_pitch_error < 8 and avg_timing_error < 0.2:
        return "Advanced Control"

    if avg_accuracy > 80 and avg_pitch_error < 15:
        return "Developing Stability"

    if avg_accuracy > 60:
        return "Unstable but Progressing"

    return "Foundational Level"
