import math

SA_FREQ = 523.25  # Middle Sa (Madhya Sa)

INT_TO_NOTE = [
    "Sa", "Komal Re", "Re", "Komal Ga", "Ga",
    "Ma", "Tivra Ma", "Pa", "Komal Dha",
    "Dha", "Komal Ni", "Ni"
]

NOTE_TO_INT = {note: index for index, note in enumerate(INT_TO_NOTE)}

OCTAVE_TO_INT = {
    "Mandra": -1,
    "Madhya": 0,
    "Taar": 1,
}

def freq_to_sargam(freq):
    if freq <= 0:
        return None, None

    # Semitone distance from Madhya Sa
    semitones_from_sa = 12 * math.log2(freq / SA_FREQ)

    nearest_semitone = round(semitones_from_sa)

    note_index = nearest_semitone % 12
    note_name = INT_TO_NOTE[note_index]

    # Determine octave band
    octave_number = nearest_semitone // 12

    if octave_number <= -1:
        octave_prefix = "Mandra"
    elif octave_number == 0:
        octave_prefix = "Madhya"
    else:
        octave_prefix = "Taar"

    full_note = f"{octave_prefix} {note_name}"

    ideal_freq = SA_FREQ * (2 ** (nearest_semitone / 12))
    cents = 1200 * math.log2(freq / ideal_freq)

    return full_note, cents


def note_to_freq(note_string):
    if not isinstance(note_string, str) or not note_string.strip():
        return None

    parts = note_string.strip().split(" ", 1)
    if len(parts) == 2:
        octave_name, swara = parts
    else:
        octave_name, swara = "Madhya", parts[0]

    semitone = NOTE_TO_INT.get(swara)
    octave = OCTAVE_TO_INT.get(octave_name, 0)

    if semitone is None:
        return None

    absolute_semitones = octave * 12 + semitone
    return SA_FREQ * (2 ** (absolute_semitones / 12))
