import numpy as np

def compute_consistency(values: list):
    if len(values) < 2:
        return 0

    variance = np.var(values)

    # invert variance to consistency score
    consistency_score = 1 / (1 + variance)

    return float(consistency_score)
