import pytest
import os

if os.getenv("RUN_AUDIO_DEVICE_TESTS", "0") != "1":
    pytest.skip(
        "Manual audio-device test. Set RUN_AUDIO_DEVICE_TESTS=1 to enable.",
        allow_module_level=True,
    )

sd = pytest.importorskip("sounddevice")

import numpy as np
import time
from backend.utils.audio.pitch_detector import detect_pitch

SAMPLERATE = 44100

def callback(indata, frames, time_info, status):
    samples = np.mean(indata, axis=1).astype(np.float32)
    freq, conf = detect_pitch(samples)

    if freq > 0 and conf > 0.8:
        print(f"Pitch: {freq:.2f} Hz | Confidence: {conf:.2f}")

def run_pitch_detector_live_test():
    print("Test Pitch Detector (Ctrl+C to stop)")
    with sd.InputStream(
        channels=1,
        samplerate=SAMPLERATE,
        blocksize=512,
        callback=callback
    ):
        while True:
            time.sleep(0.1)


if __name__ == "__main__":
    run_pitch_detector_live_test()

