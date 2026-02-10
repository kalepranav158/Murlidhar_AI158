import math

INT_TO_NOTE = [
    "Sa", "Komal Re", "Re", "Komal Ga", "Ga",
    "Ma", "Tivra Ma", "Pa", "Komal Dha",
    "Dha", "Komal Ni", "Ni"
]

SA_FREQ = None

def freq_to_sargam(freq):
    global SA_FREQ
    if freq <= 0:
        return None, None

    if SA_FREQ is None:
        SA_FREQ = freq

    cents_from_sa = 1200 * math.log2(freq / SA_FREQ)
    note_index = round(cents_from_sa / 100) % 12

    note = INT_TO_NOTE[note_index]
    ideal_freq = SA_FREQ * (2 ** (note_index / 12))
    cents = 1200 * math.log2(freq / ideal_freq)

    return note, cents
