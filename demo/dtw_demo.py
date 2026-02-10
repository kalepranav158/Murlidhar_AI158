import time
import numpy as np
import sounddevice as sd

from audio.pitch_detector import detect_pitch
from audio.note_mapper import freq_to_sargam
from audio.note_segmenter import NoteSegmenter
from dtw.aligner import dtw_align
from evaluation.scorer import evaluate

SAMPLERATE = 44100
segmenter = NoteSegmenter()
start_time = None

reference = [
    {"note": "Sa", "time": 0.0},
    {"note": "Re", "time": 0.5},
    {"note": "Ga", "time": 1.0},
    {"note": "Ma", "time": 1.5},
    {"note": "Pa", "time": 2.0},
    {"note": "Dha", "time": 2.5},
    {"note": "Ni", "time": 3.0},
    {"note": "Sa", "time": 3.5},
]

def callback(indata, frames, time_info, status):
    global start_time
    samples = np.mean(indata, axis=1).astype(np.float32)
    freq, conf = detect_pitch(samples)

    if freq <= 0 or conf < 0.8:
        return

    note, cents = freq_to_sargam(freq)
    # Ignore octave mistakes / harmonics
    if abs(cents) > 50:
        return

    if note is None:
        return

    if start_time is None:
        start_time = time.time()

    t = time.time() - start_time
    segmenter.process(note, cents, t)

print("🎵 Play Sa Re Ga Ma Pa Dha Ni Sa")

with sd.InputStream(
    channels=1,
    samplerate=SAMPLERATE,
    blocksize=512,
    callback=callback
):
    time.sleep(15)   # ⏺ record for 15 seconds

played = segmenter.get_notes()


print("\n🎼 SEGMENTED NOTES:")
for n in played:
    print(n)

if len(played) < 3:
    print("❌ Too few notes detected. Try again.")
    exit()

cost, alignment = dtw_align(reference, played)
result = evaluate(alignment)

print("\nDTW Cost:", cost)
print("Evaluation:", result)


