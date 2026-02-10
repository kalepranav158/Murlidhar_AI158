import math

# Fixed Sa for C natural flute (middle octave)
SA_FREQ = 523.25  # Hz

INT_TO_NOTE = [
    "Sa", "Komal Re", "Re", "Komal Ga", "Ga",
    "Ma", "Tivra Ma", "Pa", "Komal Dha",
    "Dha", "Komal Ni", "Ni"
]

def freq_to_sargam(freq):
    if freq <= 0:
        return None, None

    # cents relative to Sa
    cents_from_sa = 1200 * math.log2(freq / SA_FREQ)

    # fold into nearest octave
    octave_shift = round(cents_from_sa / 1200)
    cents_from_sa -= octave_shift * 1200

    note_index = round(cents_from_sa / 100) % 12
    note = INT_TO_NOTE[note_index]

    ideal_freq = SA_FREQ * (2 ** (note_index / 12))
    cents = 1200 * math.log2(freq / ideal_freq)

    return note, cents
