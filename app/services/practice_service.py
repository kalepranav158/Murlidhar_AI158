import numpy as np
import soundfile as sf
import tempfile
import os
from audio.pitch_detector import detect_pitch
from audio.note_mapper import freq_to_sargam
from audio.note_segmenter import NoteSegmenter
from dtw.aligner import dtw_align
from evaluation.scorer import evaluate
from music.song_loader import load_song
from database.db import save_session


HOP_SIZE = 512


async def evaluate_audio(upload_file, song_id, phrase_index):

    # -----------------------------
    # Load Song
    # -----------------------------
    song_path = f"songs/{song_id}.json"

    if not os.path.exists(song_path):
        return {"error": "Song not found"}

    song = load_song(song_path)

    if phrase_index >= len(song["phrases"]):
        return {"error": "Invalid phrase index"}

    phrase = song["phrases"][phrase_index]
    reference = phrase["notes"]

    # -----------------------------
    # Save Temporary WAV
    # -----------------------------
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await upload_file.read())
        tmp_path = tmp.name

    data, samplerate = sf.read(tmp_path)

    if len(data.shape) > 1:
        data = np.mean(data, axis=1)

    segmenter = NoteSegmenter()
    current_time = 0.0

    # -----------------------------
    # Frame-Based Processing
    # -----------------------------
    for i in range(0, len(data) - HOP_SIZE, HOP_SIZE):
        frame = data[i:i + HOP_SIZE].astype(np.float32)

        freq, conf = detect_pitch(frame)

        if freq <= 0 or conf < 0.8:
            current_time += HOP_SIZE / samplerate
            continue

        note, cents = freq_to_sargam(freq)

        if note and abs(cents) <= 50:
            segmenter.process(note, cents, current_time)

        current_time += HOP_SIZE / samplerate

    played = segmenter.get_notes()

    os.remove(tmp_path)

    if len(played) == 0:
        return {"error": "No valid notes detected"}

    # -----------------------------
    # DTW + Scoring
    # -----------------------------
    cost, alignment = dtw_align(reference, played)
    result = evaluate(alignment)

    save_session(reference, played, result)

    return {
        "song": song["title"],
        "phrase_index": phrase_index,
        "dtw_cost": cost,
        "evaluation": result,
        "played_notes": played
    }
