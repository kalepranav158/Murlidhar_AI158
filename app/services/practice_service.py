from fastapi import HTTPException
import os
import numpy as np
import logging
from app.services.adaptive_engine import generate_adaptive_plan
from app.services.llm.feedback_llm import generate_guru_feedback, generate_normal_feedback
from music.song_loader import load_song
from database.db import save_session, update_alankar_mastery, update_phrase_mastery, is_song_mastered
from app.services.alankar_engine import compute_alankar_level
from app.services.song_engine import generate_song_adaptive_plan
from app.services.practice_endpoint.audio_core import process_audio_core
from audio.techniques import compare_with_reference

logger = logging.getLogger(__name__)


async def evaluate_alankar(
    user_id: str,
    upload_file,
    alankar_id: str,
    phrase_index: int,
    tempo: int
):
    """
    Alankar practice evaluation service.
    
    Flow:
    1. Load alankar JSON
    2. Extract metadata
    3. Process audio core (pitch -> DTW -> evaluate)
    4. Save session
    5. Compute alankar level
    6. Update mastery
    7. Generate adaptive plan
    8. Generate feedback
    9. Return response
    """
    logger.info(f"Alankar practice: user={user_id}, alankar={alankar_id}, phrase={phrase_index}")

    # Validate tempo
    if tempo is None or tempo <= 0:
        raise HTTPException(status_code=400, detail="Valid tempo required")

    # Load alankar JSON
    song_path = f"songs/{alankar_id}.json"
    if not os.path.exists(song_path):
        raise HTTPException(status_code=404, detail="Alankar not found")

    song = load_song(song_path)
    base_tempo = song.get("base_tempo", 60)

    # Validate phrase index
    if phrase_index < 0 or phrase_index >= len(song["phrases"]):
        raise HTTPException(status_code=400, detail="Invalid phrase index")

    phrase = song["phrases"][phrase_index]
    reference = phrase["notes"]

    if not reference:
        raise HTTPException(status_code=500, detail="Reference phrase empty")

    # Process audio core (no adaptive logic here)
    cost, result, played, techniques, alignment_indices = await process_audio_core(upload_file, reference)

    # Compute real BPM from played notes
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

    reference_bpm = tempo
    if real_bpm is not None:
        tempo_deviation = real_bpm - reference_bpm

    result["real_bpm"] = float(real_bpm) if real_bpm is not None else None
    result["tempo_variance"] = tempo_variance
    result["tempo_deviation"] = float(tempo_deviation) if tempo_deviation is not None else None
    result["reference_bpm"] = reference_bpm

    # Compute session indices
    pitch_index = max(0, 1 - (result["avg_pitch_error_cents"] / 50))
    rhythm_index = max(0, 1 - (result["avg_timing_error_sec"] / 1))
    consistency_index = 1  # single session

    # Gate technique detection on accuracy (skip if performance too poor)
    if result["note_accuracy"] < 40 or result["avg_pitch_error_cents"] > 25:
        techniques = {"meend": [], "gamak": []}

    # Technique comparison with reference (phrase-level expectation)
    try:
        technique_cmp = compare_with_reference(techniques, phrase, played, alignment_indices)
        technique_score = float(technique_cmp.get("technique_score", 0.0))
    except Exception:
        logger.exception("Technique comparison failed")
        technique_cmp = {"technique_score": 0.0, "details": {}}
        technique_score = 0.0

    composite_score = (
        0.4 * (result["note_accuracy"] / 100) +
        0.3 * pitch_index +
        0.3 * rhythm_index
    )

    # Incorporate technique score: reward correct (+0.1 max), penalize missing required (-0.05)
    # If reference expects techniques but we found none -> reduce score
    has_expected_techniques = bool(phrase.get("transitions", []) and any(t.get("technique") for t in phrase.get("transitions", [])))
    if has_expected_techniques and technique_score == 0.0:
        composite_score = max(0.0, composite_score - 0.05)
    else:
        composite_score = composite_score + 0.1 * technique_score

    result["pitch_index"] = round(pitch_index, 3)
    result["rhythm_index"] = round(rhythm_index, 3)
    result["consistency_index"] = round(consistency_index, 3)
    result["composite_score"] = round(composite_score, 3)
    result["technique_score"] = round(technique_score, 3)
    result["technique_details"] = technique_cmp.get("details", {})

    # Save session
    save_session(user_id=user_id, reference=reference, played=played, result=result)

    # Alankar-specific: Compute level
    plateau_flag = False  # Will be set by adaptive plan logic
    level_info = compute_alankar_level(
        user_id=user_id,
        song=song,
        composite_score=composite_score,
        plateau_flag=plateau_flag
    )

    # Update alankar mastery
    update_alankar_mastery(
        user_id=user_id,
        alankar_id=song["id"],
        level_index=level_info["level_index"],
        tempo=level_info["recommended_tempo"],
        composite_score=composite_score
    )

    # Generate adaptive plan
    adaptive_plan = generate_adaptive_plan(
        user_id=user_id,
        base_bpm=tempo,
        real_bpm=result["real_bpm"],
        reference_bpm=result.get("reference_bpm"),
        tempo_deviation=result.get("tempo_deviation")
    )

    # Generate feedback
    try:
        ai_feedback = generate_guru_feedback(result, adaptive_plan)
    except Exception:
        logger.exception("LLM feedback failed, using fallback")
        ai_feedback = generate_normal_feedback(result)

    return {
        "song": song["title"],
        "phrase_index": phrase_index,
        "alankar_level": level_info,
        "dtw_cost": float(cost),
        "evaluation": {
            "note_accuracy": result["note_accuracy"],
            "avg_pitch_error_cents": result["avg_pitch_error_cents"],
            "avg_timing_error_sec": result["avg_timing_error_sec"],
            "mistakes": result["mistakes"],
            "feedback": ai_feedback,
        },
        "techniques": techniques,
        "technique_score": result.get("technique_score", 0.0),
        "technique_details": result.get("technique_details", {}),
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


async def evaluate_song(
    user_id: str,
    upload_file,
    song_id: str,
    phrase_index: int,
    tempo: int
):
    """
    Song practice evaluation service.
    
    Flow:
    1. Load song JSON
    2. Extract metadata
    3. Process audio core (pitch -> DTW -> evaluate)
    4. Save session
    5. Update phrase mastery
    6. Generate song adaptive plan
    7. Check full unlock
    8. Generate adaptive plan
    9. Generate feedback
    10. Return response
    """
    logger.info(f"Song practice: user={user_id}, song={song_id}, phrase={phrase_index}")

    # Validate tempo
    if tempo is None or tempo <= 0:
        raise HTTPException(status_code=400, detail="Valid tempo required")

    # Load song JSON
    song_path = f"songs/{song_id}.json"
    if not os.path.exists(song_path):
        raise HTTPException(status_code=404, detail="Song not found")

    song = load_song(song_path)
    base_tempo = song.get("base_tempo", 60)

    # Validate phrase index
    if phrase_index < 0 or phrase_index >= len(song["phrases"]):
        raise HTTPException(status_code=400, detail="Invalid phrase index")

    phrase = song["phrases"][phrase_index]
    reference = phrase["notes"]

    if not reference:
        raise HTTPException(status_code=500, detail="Reference phrase empty")

    # Process audio core (no adaptive logic here)
    cost, result, played, techniques, alignment_indices = await process_audio_core(upload_file, reference)

    # Compute real BPM from played notes
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

    reference_bpm = tempo
    if real_bpm is not None:
        tempo_deviation = real_bpm - reference_bpm

    result["real_bpm"] = float(real_bpm) if real_bpm is not None else None
    result["tempo_variance"] = tempo_variance
    result["tempo_deviation"] = float(tempo_deviation) if tempo_deviation is not None else None
    result["reference_bpm"] = reference_bpm

    # Compute session indices
    pitch_index = max(0, 1 - (result["avg_pitch_error_cents"] / 50))
    rhythm_index = max(0, 1 - (result["avg_timing_error_sec"] / 1))
    consistency_index = 1  # single session

    # Gate technique detection on accuracy (skip if performance too poor)
    if result["note_accuracy"] < 40 or result["avg_pitch_error_cents"] > 25:
        techniques = {"meend": [], "gamak": []}

    # Technique comparison with reference (phrase-level expectation)
    try:
        technique_cmp = compare_with_reference(techniques, phrase, played, alignment_indices)
        technique_score = float(technique_cmp.get("technique_score", 0.0))
    except Exception:
        logger.exception("Technique comparison failed")
        technique_cmp = {"technique_score": 0.0, "details": {}}
        technique_score = 0.0

    composite_score = (
        0.4 * (result["note_accuracy"] / 100) +
        0.3 * pitch_index +
        0.3 * rhythm_index
    )

    # Incorporate technique score: reward correct (+0.1 max), penalize missing required (-0.05)
    # If reference expects techniques but we found none -> reduce score
    has_expected_techniques = bool(phrase.get("transitions", []) and any(t.get("technique") for t in phrase.get("transitions", [])))
    if has_expected_techniques and technique_score == 0.0:
        composite_score = max(0.0, composite_score - 0.05)
    else:
        composite_score = composite_score + 0.1 * technique_score

    result["pitch_index"] = round(pitch_index, 3)
    result["rhythm_index"] = round(rhythm_index, 3)
    result["consistency_index"] = round(consistency_index, 3)
    result["composite_score"] = round(composite_score, 3)
    result["technique_score"] = round(technique_score, 3)
    result["technique_details"] = technique_cmp.get("details", {})

    # Save session
    save_session(user_id=user_id, reference=reference, played=played, result=result)

    # Song-specific: Update phrase mastery
    update_phrase_mastery(
        user_id=user_id,
        song_id=song["id"],
        phrase_id=phrase_index,
        accuracy=result["note_accuracy"],
        pitch_error=result["avg_pitch_error_cents"],
        timing_error=result["avg_timing_error_sec"]
    )

    # Check if full song is unlocked
    full_song_unlocked = is_song_mastered(
        user_id=user_id,
        song_id=song["id"],
        total_phrases=len(song["phrases"])
    )

    # Generate song adaptive plan
    song_adaptive_plan = generate_song_adaptive_plan(
        user_id=user_id,
        song=song,
        phrase_index=phrase_index,
        accuracy=result["note_accuracy"],
        base_tempo=base_tempo
    )

    # Generate general adaptive plan
    adaptive_plan = generate_adaptive_plan(
        user_id=user_id,
        base_bpm=tempo,
        real_bpm=result["real_bpm"],
        reference_bpm=result.get("reference_bpm"),
        tempo_deviation=result.get("tempo_deviation")
    )

    # Generate feedback
    try:
        ai_feedback = generate_guru_feedback(result, adaptive_plan)
    except Exception:
        logger.exception("LLM feedback failed, using fallback")
        ai_feedback = generate_normal_feedback(result)

    return {
        "song": song["title"],
        "phrase_index": phrase_index,
        "dtw_cost": float(cost),
        "evaluation": {
            "note_accuracy": result["note_accuracy"],
            "avg_pitch_error_cents": result["avg_pitch_error_cents"],
            "avg_timing_error_sec": result["avg_timing_error_sec"],
            "mistakes": result["mistakes"],
            "feedback": ai_feedback,
        },
        "techniques": techniques,
        "technique_score": result.get("technique_score", 0.0),
        "technique_details": result.get("technique_details", {}),
        "adaptive_plan": adaptive_plan,
        "song_adaptive_plan": song_adaptive_plan,
        "full_song_unlocked": full_song_unlocked,
        "played_notes": [
            {
                "note": n["note"],
                "cents": float(n["cents"]),
                "time": float(n["time"])
            }
            for n in played
        ]
    }




def build_full_song_reference(song: dict):
    full_reference = []
    boundaries = []

    index = 0

    for phrase in song["phrases"]:
        full_reference.extend(phrase["notes"])
        index += len(phrase["notes"])
        boundaries.append(index)

    return full_reference, boundaries


async def evaluate_song_full(user_id, upload_file, song_id, tempo):

    song_path = f"songs/{song_id}.json"

    if not os.path.exists(song_path):
        raise HTTPException(status_code=404, detail="Song not found")

    song = load_song(song_path)

    if song.get("type") != "song":
        raise HTTPException(status_code=400, detail="Not a song")

    # Check unlock
    if not is_song_mastered(user_id, song["id"], len(song["phrases"])):
        raise HTTPException(403, "Master all phrases before full performance.")

    full_reference, boundaries = build_full_song_reference(song)

    cost, result, played, techniques, alignment_indices = await process_audio_core(upload_file, full_reference)
    transition_score = compute_transition_score(played, boundaries, tempo=tempo)
    flow_score = compute_flow_consistency(played)

    # No phrase-level reference for full song; aggregate technique scoring not implemented yet
    technique_cmp = compare_with_reference(techniques, None, played, alignment_indices)
    technique_score = float(technique_cmp.get("technique_score", 0.0))

    save_session(user_id=user_id, reference=full_reference, played=played, result=result)

    # Full-song adaptive logic can be added later
    return {
        "mode": "full_song",
        "song": song["title"],
        "dtw_cost": float(cost),
        "transition_score": transition_score,
        "flow_score": flow_score,
        "techniques": techniques,
        "technique_score": technique_score,
        "evaluation": {
            "note_accuracy": result["note_accuracy"],
            "avg_pitch_error_cents": result["avg_pitch_error_cents"],
            "avg_timing_error_sec": result["avg_timing_error_sec"],
            "mistakes": result["mistakes"],
        },
        "played_notes": played
    }


def compute_transition_score(played_notes, boundaries, tempo=60):
    """Compute smooth transitions between phrases, tempo-aware.
    
    Expected gap between phrases is tempo-dependent:
    - Ideal gap ~= 1-2 quarter note durations
    - At 60 BPM, quarter note = 1 sec, so ideal gap ~= 1-2 sec
    - At 120 BPM, quarter note = 0.5 sec, so ideal gap ~= 0.5-1 sec
    """
    if len(boundaries) <= 1:
        return 1.0

    gaps = []

    for boundary in boundaries[:-1]:
        if boundary < len(played_notes):
            t1 = played_notes[boundary - 1]["time"]
            t2 = played_notes[boundary]["time"]
            gap = abs(t2 - t1)
            gaps.append(gap)

    if not gaps:
        return 1.0

    avg_gap = sum(gaps) / len(gaps)

    # Tempo-aware normalization: ideal gap = 2 * (60 / tempo) seconds
    # At 60 BPM: ideal ~= 2 sec; at 120 BPM: ideal ~= 1 sec
    ideal_gap = 2.0 * (60.0 / max(30, tempo))  # clamp tempo to avoid division issues
    score = max(0, 1 - (avg_gap / (2 * ideal_gap)))
    return round(score, 3)






def compute_flow_consistency(played_notes):
    """Compute rhythm consistency (how steady the tempo is).
    
    Normalized variance: compare actual variance to expected variance for random timing.
    Lower normalized variance = better consistency.
    """
    if len(played_notes) < 3:
        return 1.0

    intervals = []

    for i in range(1, len(played_notes)):
        intervals.append(
            played_notes[i]["time"] - played_notes[i - 1]["time"]
        )

    if not intervals:
        return 1.0

    mean_interval = sum(intervals) / len(intervals)
    if mean_interval <= 0:
        return 1.0

    variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
    
    # Normalize variance by mean_interval^2 to make it dimensionless [0, inf)
    # Then clamp to [0, 1] range for score
    normalized_variance = variance / (mean_interval ** 2) if mean_interval > 0 else 0
    score = max(0, 1 - normalized_variance)
    return round(score, 3)    