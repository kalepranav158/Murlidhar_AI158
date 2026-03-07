from statistics import median, pstdev


NOTE_TO_INT = {
    "Sa": 0,
    "Komal Re": 1,
    "Re": 2,
    "Komal Ga": 3,
    "Ga": 4,
    "Ma": 5,
    "Tivra Ma": 6,
    "Pa": 7,
    "Komal Dha": 8,
    "Dha": 9,
    "Komal Ni": 10,
    "Ni": 11,
}

OCTAVE_TO_INT = {
    "Mandra": -1,
    "Madhya": 0,
    "Taar": 1,
}


def _note_to_index(note_string: str):
    parts = (note_string or "").split(" ", 1)
    if len(parts) == 2:
        octave, base_note = parts
    else:
        octave, base_note = "Madhya", parts[0] if parts else ""

    if base_note not in NOTE_TO_INT:
        return None

    return OCTAVE_TO_INT.get(octave, 0) * 12 + NOTE_TO_INT[base_note]


def _compute_transposition_accuracy(alignment):
    semitone_diffs = []
    indexed_pairs = []

    for ref, play in alignment:
        ref_idx = _note_to_index(ref.get("note", ""))
        play_idx = _note_to_index(play.get("note", ""))
        if ref_idx is None or play_idx is None:
            continue

        diff = play_idx - ref_idx
        semitone_diffs.append(diff)
        indexed_pairs.append((ref_idx, play_idx))

    if not indexed_pairs:
        return None

    tonic_shift = int(round(median(semitone_diffs)))
    shift_stability = pstdev(semitone_diffs) if len(semitone_diffs) > 1 else 0.0

    corrected_matches = 0
    for ref_idx, play_idx in indexed_pairs:
        if ref_idx == (play_idx - tonic_shift):
            corrected_matches += 1

    corrected_accuracy = round(100 * corrected_matches / len(indexed_pairs), 2)

    return {
        "accuracy": corrected_accuracy,
        "tonic_shift": tonic_shift,
        "stability": shift_stability,
    }


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

    transposed = _compute_transposition_accuracy(alignment)
    if (
        transposed
        and transposed["accuracy"] > note_accuracy
        and transposed["stability"] <= 0.5
    ):
        note_accuracy = transposed["accuracy"]

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
