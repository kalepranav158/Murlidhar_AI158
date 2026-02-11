import math

SA_FREQ = 523.25  # Middle Sa (Madhya Sa)

INT_TO_NOTE = [
    "Sa", "Komal Re", "Re", "Komal Ga", "Ga",
    "Ma", "Tivra Ma", "Pa", "Komal Dha",
    "Dha", "Komal Ni", "Ni"
]

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
