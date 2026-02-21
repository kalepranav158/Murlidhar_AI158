from fastapi import HTTPException
import numpy as np
import soundfile as sf
import tempfile
import os
import logging
from app.services.adaptive_engine import generate_adaptive_plan
from app.services.llm.feedback_llm import generate_guru_feedback, generate_normal_feedback
from audio.pitch_detector import detect_pitch
from audio.note_mapper import freq_to_sargam
from audio.note_segmenter import NoteSegmenter
from dtw.aligner import dtw_align
from evaluation.scorer import evaluate
from music.song_loader import load_song
from database.db import save_session

logger = logging.getLogger(__name__)

HOP_SIZE = 512

async def evaluate_audio(user_id,upload_file, song_id, phrase_index,tempo):

    logger.info(f"Practice request: song={song_id}, phrase={phrase_index}")

    #validate Tempo value
    if tempo is None or tempo <= 0:
        raise HTTPException(status_code=400, detail="Valid tempo required")
    
    
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

# ------------Real Tempo Extraction-----------------------------------------------------------------------------------------
        real_bpm = None
        tempo_variance = None
        tempo_deviation = None

        if len(played) >= 2:
            note_times = [n["time"] for n in played]
            intervals = np.diff(note_times)

            if len(intervals) > 0:
                mean_interval = np.mean(intervals)

                if mean_interval > 0:
                    real_bpm = 60 / mean_interval
                    tempo_variance = float(np.std(intervals))

        reference_bpm = tempo  # ← USER PASSED TEMPO

        if real_bpm is not None:
            tempo_deviation = real_bpm - reference_bpm

        result["real_bpm"] = float(real_bpm) if real_bpm else None
        result["tempo_variance"] = tempo_variance
        result["tempo_deviation"] = float(tempo_deviation) if tempo_deviation else None
        result["reference_bpm"] = reference_bpm
        print(f"Real BPM: {real_bpm}, Reference BPM: {reference_bpm}, Tempo Deviation: {tempo_deviation}")
    except Exception:
        logger.exception("DTW evaluation failed")
        raise HTTPException(status_code=500, detail="Evaluation failed")
#---------------------------------------------------------------------------------------------------

    save_session(user_id=user_id, reference=reference, played=played, result=result)

    logger.info(f"Detected {len(played)} notes. DTW cost={cost}")
    


    # generate feedback using LLM with fallback
    try:
        ai_feedback = generate_guru_feedback(result)
    except Exception:
       logger.exception("LLM failed, using fallback feedback")
       ai_feedback = generate_normal_feedback(result)
    
    adaptive_plan = generate_adaptive_plan(
    user_id=user_id,
    base_bpm=tempo,
    real_bpm=result["real_bpm"],
    reference_bpm=result.get("reference_bpm"),
    tempo_deviation=result.get("tempo_deviation")
)

    print(f"Adaptive Plan: {adaptive_plan}")
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
        "adaptive_plan": adaptive_plan,
        "played_notes": [
            {
                "note": n["note"],
                "cents": float(n["cents"]),
                "time": float(n["time"])
            }
            for n in played
        ]
    }




