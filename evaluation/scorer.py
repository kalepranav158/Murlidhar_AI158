def evaluate(alignment):
    """
    Evaluate a DTW alignment between reference notes and played notes.

    Metrics:
    - note_accuracy (% correct notes)
    - avg_pitch_error_cents (mean absolute cents deviation)
    - avg_timing_error_sec (mean difference in relative note durations)
    """

    if len(alignment) == 0:
        return {
            "note_accuracy": 0.0,
            "avg_pitch_error_cents": None,
            "avg_timing_error_sec": None,
            "mistakes": [],
            "message": "No valid note alignment detected. Play slower and clearer."
        }

    correct = 0
    pitch_errors = []
    mistakes = []

    # --- note + pitch evaluation ---
    for ref, play in alignment:
        if ref["note"] == play["note"]:
            correct += 1
        else:
            mistakes.append({
                "expected": ref["note"],
                "played": play["note"]
            })

        pitch_errors.append(abs(play["cents"]))

    note_accuracy = round(100 * correct / len(alignment), 2)
    avg_pitch_error = round(sum(pitch_errors) / len(pitch_errors), 2)

    # --- relative timing evaluation (IOI-based) ---
    if len(alignment) < 2:
        avg_timing_error = 0.0
    else:
        ref_durations = []
        play_durations = []

        for i in range(len(alignment) - 1):
            ref_t1 = alignment[i][0]["time"]
            ref_t2 = alignment[i + 1][0]["time"]
            play_t1 = alignment[i][1]["time"]
            play_t2 = alignment[i + 1][1]["time"]

            ref_durations.append(ref_t2 - ref_t1)
            play_durations.append(play_t2 - play_t1)

        timing_errors = [
            abs(r - p) for r, p in zip(ref_durations, play_durations)
        ]

        avg_timing_error = round(
            sum(timing_errors) / len(timing_errors), 2
        )

    return {
        "note_accuracy": note_accuracy,
        "avg_pitch_error_cents": avg_pitch_error,
        "avg_timing_error_sec": avg_timing_error,
        "mistakes": mistakes
    }
