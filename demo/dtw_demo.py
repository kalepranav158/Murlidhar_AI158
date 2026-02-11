import time
import numpy as np
import sounddevice as sd

from audio.pitch_detector import detect_pitch
from audio.note_mapper import freq_to_sargam
from audio.note_segmenter import NoteSegmenter
from dtw.aligner import dtw_align
from evaluation.scorer import evaluate
from database.db import init_db, save_session


SAMPLERATE = 44100
BLOCKSIZE = 512
RECORD_SECONDS = 15


def main():
    init_db()  # ✅ ensure DB exists

    segmenter = NoteSegmenter()
    start_time = None

    reference = [
        {"note": "Madhya Sa", "time": 0.0},
        {"note": "Madhya Re", "time": 0.5},
        {"note": "Madhya Ga", "time": 1.0},
        {"note": "Madhya Ma", "time": 1.5},
        {"note": "Madhya Pa", "time": 2.0},
        {"note": "Madhya Dha", "time": 2.5},
        {"note": "Madhya Ni", "time": 3.0},
        {"note": "Taar Sa", "time": 3.5},
    ]

    def callback(indata, frames, time_info, status):
        nonlocal start_time

        samples = np.mean(indata, axis=1).astype(np.float32)
        freq, conf = detect_pitch(samples)

        if freq <= 0 or conf < 0.8:
            return

        note, cents = freq_to_sargam(freq)

        if note is None:
            return

        if abs(cents) > 50:
            return

        if start_time is None:
            start_time = time.time()

        t = time.time() - start_time
        segmenter.process(note, cents, t)

    print("🎵 Play Sa Re Ga Ma Pa Dha Ni Sa")

    with sd.InputStream(
        channels=1,
        samplerate=SAMPLERATE,
        blocksize=BLOCKSIZE,
        callback=callback
    ):
        time.sleep(RECORD_SECONDS)

    played = segmenter.get_notes()

    print("\n🎼 SEGMENTED NOTES:")
    for n in played:
        print(n)

    if len(played) < 3:
        print("❌ Too few notes detected. Try again.")
        return

    cost, alignment = dtw_align(reference, played)
    result = evaluate(alignment)

    print("\nDTW Cost:", cost)
    print("Evaluation:", result)

    # ✅ Save session
    save_session(reference, played, result)
    print("💾 Session saved to database.")


if __name__ == "__main__":
    main()
