"""
Audio Core Module — Handles pitch detection, note segmentation, DTW alignment, and evaluation.
Pure audio processing logic, no business logic or database dependencies.
"""

import logging
import os
import tempfile
from typing import Tuple, Dict, List, Any

import numpy as np
import soundfile as sf
from fastapi import HTTPException

from audio.pitch_detector import detect_pitch
from audio.note_mapper import freq_to_sargam
from audio.note_segmenter import NoteSegmenter
from audio.techniques import detect_techniques
from dtw.aligner import dtw_align
from evaluation.scorer import evaluate

logger = logging.getLogger(__name__)

HOP_SIZE = 512
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


async def process_audio_core(
    upload_file,
    reference: List[Dict[str, Any]]
) -> Tuple[float, Dict[str, Any], List[Dict[str, Any]], Dict[str, Any], List[Tuple[int, int]]]:
    """
    Core audio processing pipeline.
    
    Args:
        upload_file: FastAPI UploadFile object
        reference: List of reference notes (notes dict from song/alankar phrase)
    
    Returns:
        Tuple[cost, result, played, techniques, alignment_path]
        - cost: DTW alignment cost
        - result: Evaluation metrics (note_accuracy, pitch error, timing error, etc.)
        - played: List of detected notes with time and pitch info
        - techniques: Detected expressive techniques (meend, gamak)
        - alignment_path: DTW alignment as [(played_idx, reference_idx), ...]
    
    Raises:
        HTTPException: On file validation, processing, or evaluation errors
    """

    # ==========================================
    # Step 1: Validate File Type & Size
    # ==========================================
    if upload_file.content_type not in ["audio/wav", "audio/x-wav"]:
        raise HTTPException(status_code=400, detail="Only WAV files supported")

    contents = await upload_file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    # ==========================================
    # Step 2: Save & Load Audio Temporarily
    # ==========================================
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        data, samplerate = sf.read(tmp_path)

        # Convert stereo to mono if needed
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

    except Exception as e:
        logger.exception("Audio file read failed")
        raise HTTPException(status_code=500, detail="Audio file read failed")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    # ==========================================
    # Step 3: Pitch Detection & Segmentation
    # ==========================================
    try:
        segmenter = NoteSegmenter()
        current_time = 0.0

        # store raw pitch contour per frame for technique detection
        pitch_contour = []

        for i in range(0, len(data) - HOP_SIZE, HOP_SIZE):
            frame = data[i : i + HOP_SIZE].astype(np.float32)

            freq, conf = detect_pitch(frame)

            # record available pitch info (freq>0) regardless of segmentation confidence
            if freq and freq > 0:
                pitch_contour.append({"freq": float(freq), "time": float(current_time), "conf": float(conf)})

            # Skip frames with no pitch
            if freq <= 0:
                current_time += HOP_SIZE / samplerate
                continue

            # Skip low-confidence frames for segmentation only
            if conf < 0.8:
                current_time += HOP_SIZE / samplerate
                continue

            note, cents = freq_to_sargam(freq)

            # Accept notes within ±50 cents (half-step tolerance)
            if note and abs(cents) <= 50:
                segmenter.process(note, cents, current_time)

            current_time += HOP_SIZE / samplerate

        played = segmenter.get_notes()

    except Exception as e:
        logger.exception("Pitch detection/segmentation failed")
        raise HTTPException(status_code=500, detail="Audio processing failed")

    # ==========================================
    # Step 4: Validate Detected Notes
    # ==========================================
    if not played:
        raise HTTPException(status_code=400, detail="No valid notes detected")

    # ==========================================
    # Step 5: DTW Alignment & Evaluation
    # ==========================================
    try:
        cost, alignment = dtw_align(reference, played)
        result = evaluate(alignment)
        
        # Convert alignment (ref_note, played_note) tuples to (played_idx, ref_idx) indices
        # so we can map time-based technique windows to reference space
        alignment_indices = []
        for ref_note, played_note in alignment:
            # Find indices by comparing note objects
            ref_idx = next((i for i, n in enumerate(reference) if n is ref_note), None)
            played_idx = next((i for i, n in enumerate(played) if n is played_note), None)
            if ref_idx is not None and played_idx is not None:
                alignment_indices.append((played_idx, ref_idx))

    except Exception as e:
        logger.exception("DTW evaluation failed")
        raise HTTPException(status_code=500, detail="Evaluation failed")

    logger.info(f"Audio core: Detected {len(played)} notes, DTW cost={cost}")

    # Detect expressive techniques from raw pitch contour
    try:
        techniques = detect_techniques(pitch_contour)
    except Exception:
        logger.exception("Technique detection failed")
        techniques = {"meend": [], "gamak": []}

    return cost, result, played, techniques, alignment_indices
