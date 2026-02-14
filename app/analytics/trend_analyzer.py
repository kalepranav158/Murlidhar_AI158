import numpy as np

def compute_trend(values: list):
    """
    Returns slope of trend line.
    Positive slope = improvement (for accuracy)
    Negative slope = improvement (for error metrics)
    """

    if len(values) < 2:
        return 0

    x = np.arange(len(values))
    y = np.array(values)

    slope = np.polyfit(x, y, 1)[0]
    return float(slope)
