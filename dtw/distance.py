NOTE_TO_INT = {
    "Sa": 0, "Komal Re": 1, "Re": 2, "Komal Ga": 3,
    "Ga": 4, "Ma": 5, "Tivra Ma": 6, "Pa": 7,
    "Komal Dha": 8, "Dha": 9, "Komal Ni": 10, "Ni": 11
}

def note_distance(ref, play):
    note_diff = abs(
        NOTE_TO_INT[ref["note"]] - NOTE_TO_INT[play["note"]]
    ) / 12.0

    pitch_diff = min(abs(play["cents"]) / 50.0, 1.0)

    return 0.7 * note_diff + 0.3 * pitch_diff

