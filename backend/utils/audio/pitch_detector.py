import numpy as np

try:
    import aubio
except ModuleNotFoundError:  # pragma: no cover - depends on local audio deps.
    aubio = None

SAMPLERATE = 44100
WIN_S = 2048
HOP_S = 512

_PITCH_DETECTOR_CACHE = {}


def _get_pitch_detector(samplerate: int):
    if aubio is None:
        raise RuntimeError(
            "aubio is not installed. Install audio dependencies to enable pitch detection."
        )

    safe_samplerate = int(samplerate) if samplerate and samplerate > 0 else SAMPLERATE
    detector = _PITCH_DETECTOR_CACHE.get(safe_samplerate)
    if detector is not None:
        return detector

    detector = aubio.pitch("yin", WIN_S, HOP_S, safe_samplerate)
    detector.set_unit("Hz")
    detector.set_silence(-40)
    _PITCH_DETECTOR_CACHE[safe_samplerate] = detector
    return detector


def detect_pitch(samples: np.ndarray, samplerate: int = SAMPLERATE):
    if len(samples) != HOP_S:
        return 0.0, 0.0

    detector = _get_pitch_detector(samplerate)
    freq = detector(samples)[0]
    confidence = detector.get_confidence()
    return freq, confidence


