NOTE_TO_INT = {
    "Sa": 0, "Komal Re": 1, "Re": 2, "Komal Ga": 3,
    "Ga": 4, "Ma": 5, "Tivra Ma": 6, "Pa": 7,
    "Komal Dha": 8, "Dha": 9, "Komal Ni": 10, "Ni": 11
}

OCTAVE_TO_INT = {
    "Mandra": -1,
    "Madhya": 0,
    "Taar": 1
}

def split_note(note_string):
    parts = note_string.split(" ", 1)
    if len(parts) == 2:
        octave, base_note = parts
    else:
        octave = "Madhya"
        base_note = parts[0]
    return octave, base_note


def note_distance(ref, play):
    ref_oct, ref_note = split_note(ref["note"])
    play_oct, play_note = split_note(play["note"])

    # Base note difference
    note_diff = abs(
        NOTE_TO_INT.get(ref_note, 0) -
        NOTE_TO_INT.get(play_note, 0)
    ) / 12.0

    # Octave difference penalty
    octave_diff = abs(
        OCTAVE_TO_INT.get(ref_oct, 0) -
        OCTAVE_TO_INT.get(play_oct, 0)
    )

    # Pitch fine tuning
    pitch_penalty = min(abs(play["cents"]) / 50.0, 1.0)

    return (
        0.6 * note_diff +
        0.3 * pitch_penalty +
        0.1 * octave_diff
    )
