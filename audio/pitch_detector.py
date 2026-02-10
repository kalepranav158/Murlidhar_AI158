import aubio
import numpy as np

SAMPLERATE = 44100
WIN_S = 2048
HOP_S = 512

pitch_o = aubio.pitch("yin", WIN_S, HOP_S, SAMPLERATE)
pitch_o.set_unit("Hz")
pitch_o.set_silence(-40)

def detect_pitch(samples: np.ndarray):
    if len(samples) != 512:
        return 0.0, 0.0

    freq = pitch_o(samples)[0]
    confidence = pitch_o.get_confidence()
    return freq, confidence
