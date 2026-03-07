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


def note_to_index(note_string):
    octave, base_note = split_note(note_string)
    base = NOTE_TO_INT.get(base_note)
    if base is None:
        return None
    return (OCTAVE_TO_INT.get(octave, 0) * 12) + base


def note_distance(ref, play, transposition_shift: int = 0):
    ref_idx = note_to_index(ref.get("note", ""))
    play_idx = note_to_index(play.get("note", ""))

    if ref_idx is not None and play_idx is not None:
        play_adjusted = play_idx - transposition_shift
        semitone_diff = abs(ref_idx - play_adjusted)
        note_diff = min(semitone_diff, 12) / 12.0
        octave_diff = abs((ref_idx // 12) - (play_adjusted // 12))
    else:
        ref_oct, ref_note = split_note(ref.get("note", ""))
        play_oct, play_note = split_note(play.get("note", ""))

        note_diff = abs(
            NOTE_TO_INT.get(ref_note, 0) -
            NOTE_TO_INT.get(play_note, 0)
        ) / 12.0

        octave_diff = abs(
            OCTAVE_TO_INT.get(ref_oct, 0) -
            OCTAVE_TO_INT.get(play_oct, 0)
        )

    # Pitch fine tuning
    cents = play.get("cents", 0.0)
    pitch_penalty = min(abs(cents) / 50.0, 1.0)

    return (
        0.6 * note_diff +
        0.3 * pitch_penalty +
        0.1 * octave_diff
    )
