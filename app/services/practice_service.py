from fastapi import HTTPException
import numpy as np
import soundfile as sf
import tempfile
import os
import logging
from app.services.llm.feedback_llm import generate_guru_feedback
from audio.pitch_detector import detect_pitch
from audio.note_mapper import freq_to_sargam
from audio.note_segmenter import NoteSegmenter
from dtw.aligner import dtw_align
from evaluation.scorer import evaluate
from music.song_loader import load_song
from database.db import save_session
from app.services.feedback import generate_feedback
from app.routes.analytics import get_summary

logger = logging.getLogger(__name__)

HOP_SIZE = 512



async def evaluate_audio(user_id,upload_file, song_id, phrase_index):

    logger.info(f"Practice request: song={song_id}, phrase={phrase_index}")

    # ----------------------------------
    # Validate File Type
    # ----------------------------------
    if upload_file.content_type not in ["audio/wav", "audio/x-wav"]:
        raise HTTPException(status_code=400, detail="Only WAV files supported")

    # ----------------------------------
    # Validate File Size (STEP 5 ADDED)
    # ----------------------------------
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    contents = await upload_file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    # ----------------------------------
    # Load Song
    # ----------------------------------
    song_path = f"songs/{song_id}.json"

    if not os.path.exists(song_path):
        raise HTTPException(status_code=404, detail="Song not found")

    song = load_song(song_path)

    if phrase_index < 0 or phrase_index >= len(song["phrases"]):
        raise HTTPException(status_code=400, detail="Invalid phrase index")

    phrase = song["phrases"][phrase_index]
    reference = phrase["notes"]

    if not reference:
        raise HTTPException(status_code=500, detail="Reference phrase empty")




    # ----------------------------------
    # Save Temporary File Safely
    # ----------------------------------
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        data, samplerate = sf.read(tmp_path)

        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        segmenter = NoteSegmenter()
        current_time = 0.0

        # ----------------------------------
        # Frame Processing
        # ----------------------------------
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

    except Exception:
        logger.exception("Audio processing failed")
        raise HTTPException(status_code=500, detail="Audio processing failed")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)





    # ----------------------------------
    # Validate Played Notes
    # ----------------------------------
    if not played:
        raise HTTPException(status_code=400, detail="No valid notes detected")



    # ----------------------------------
    # DTW + Evaluation
    # ----------------------------------
    try:
        cost, alignment = dtw_align(reference, played)
        result = evaluate(alignment)
    except Exception:
        logger.exception("DTW evaluation failed")
        raise HTTPException(status_code=500, detail="Evaluation failed")

    save_session(user_id=user_id, reference=reference, played=played, result=result)

    logger.info(f"Detected {len(played)} notes. DTW cost={cost}")
    


    # generate feedback using LLM with fallback
    try:
        ai_feedback = generate_guru_feedback(result)
    except Exception:
       logger.exception("LLM failed, using fallback feedback")
       ai_feedback = generate_feedback(result)



    return {
        "song": song["title"],
        "phrase_index": phrase_index,
        "dtw_cost": float(cost),
        "evaluation": {
            "note_accuracy": result["note_accuracy"],
            "avg_pitch_error_cents": result["avg_pitch_error_cents"],
            "avg_timing_error_sec": result["avg_timing_error_sec"],
            "mistakes": result["mistakes"],
            "feedback":ai_feedback,
        },
        "played_notes": [
            {
                "note": n["note"],
                "cents": float(n["cents"]),
                "time": float(n["time"])
            }
            for n in played
        ]
    }