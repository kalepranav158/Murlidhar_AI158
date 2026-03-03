import numpy as np
from dtw.distance import note_distance, note_to_index


def estimate_transposition_shift(reference, played):
    if not reference or not played:
        return 0

    sample_count = min(len(reference), len(played), 24)
    if sample_count < 2:
        return 0

    def sample_pair(index):
        ref_idx = int(round(index * (len(reference) - 1) / max(sample_count - 1, 1)))
        play_idx = int(round(index * (len(played) - 1) / max(sample_count - 1, 1)))
        return reference[ref_idx], played[play_idx]

    has_indexed_notes = False
    for idx in range(sample_count):
        ref_note, play_note = sample_pair(idx)
        if note_to_index(ref_note.get("note", "")) is not None and note_to_index(play_note.get("note", "")) is not None:
            has_indexed_notes = True
            break

    if not has_indexed_notes:
        return 0

    best_shift = 0
    best_cost = np.inf

    for shift in range(-12, 13):
        cost = 0.0
        for idx in range(sample_count):
            ref_note, play_note = sample_pair(idx)
            cost += note_distance(ref_note, play_note, transposition_shift=shift)

        if cost < best_cost:
            best_cost = cost
            best_shift = shift

    return best_shift


def dtw_align(reference, played):
    n, m = len(reference), len(played)
    dtw = np.full((n+1, m+1), np.inf)
    dtw[0, 0] = 0
    path = {}
    transposition_shift = estimate_transposition_shift(reference, played)

    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = note_distance(reference[i-1], played[j-1], transposition_shift=transposition_shift)
            choices = [
                (dtw[i-1, j], (i-1, j)),
                (dtw[i, j-1], (i, j-1)),
                (dtw[i-1, j-1], (i-1, j-1))
            ]
            prev_cost, prev = min(choices, key=lambda x: x[0])
            dtw[i, j] = cost + prev_cost
            path[(i, j)] = prev

    alignment = []
    i, j = n, m
    while i > 0 and j > 0:
        pi, pj = path[(i, j)]
        if pi == i-1 and pj == j-1:
            alignment.append((reference[i-1], played[j-1]))
        i, j = pi, pj

    return dtw[n, m], alignment[::-1]
