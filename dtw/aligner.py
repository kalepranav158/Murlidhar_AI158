import numpy as np
from dtw.distance import note_distance

def dtw_align(reference, played):
    n, m = len(reference), len(played)
    dtw = np.full((n+1, m+1), np.inf)
    dtw[0, 0] = 0
    path = {}

    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = note_distance(reference[i-1], played[j-1])
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
