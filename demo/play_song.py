import time
import numpy as np
import sounddevice as sd

from audio.pitch_detector import detect_pitch
from audio.note_mapper import freq_to_sargam
from audio.note_segmenter import NoteSegmenter
from dtw.aligner import dtw_align
from evaluation.scorer import evaluate
from music.song_loader import load_song
from music.reference_builder import phrase_to_reference
from database.db import init_db, save_session

SAMPLERATE = 44100
BLOCKSIZE = 512
RECORD_SECONDS = 10


def record_phrase():
    segmenter = NoteSegmenter()
    start_time = None

    def callback(indata, frames, time_info, status):
        nonlocal start_time

        samples = np.mean(indata, axis=1).astype(np.float32)
        freq, conf = detect_pitch(samples)

        if freq <= 0 or conf < 0.8:
            return

        note, cents = freq_to_sargam(freq)

        if note is None or abs(cents) > 50:
            return

        if start_time is None:
            start_time = time.time()

        t = time.time() - start_time
        segmenter.process(note, cents, t)

    with sd.InputStream(
        channels=1,
        samplerate=SAMPLERATE,
        blocksize=BLOCKSIZE,
        callback=callback
    ):
        time.sleep(RECORD_SECONDS)

    return segmenter.get_notes()


def main():
    init_db()

    song = load_song("songs/basic_alankar.json")

    print(f"\n🎵 Playing Song: {song['title']}\n")

    for idx, phrase in enumerate(song["phrases"]):
        print(f"\n--- Phrase {idx+1} ---")
        reference = phrase_to_reference(phrase)

        print("🎶 Play this phrase:")
        for note in phrase:
            print(note["note"], end=" ")
        print("\nRecording...")

        played = record_phrase()

        print("\nDetected Notes:")
        for n in played:
            print(n)

        if len(played) < 2:
            print("Too few notes detected.")
            continue

        cost, alignment = dtw_align(reference, played)
        result = evaluate(alignment)

        print("\nEvaluation:", result)
        save_session(reference, played, result)
        print("💾 Phrase saved.")


if __name__ == "__main__":
    main()
