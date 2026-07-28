"""
Audio Core Module â€” Handles pitch detection, note segmentation, DTW alignment, and evaluation.
Pure audio processing logic, no business logic or database dependencies.
"""

import logging
import math
import os
import tempfile
from typing import Tuple, Dict, List, Any

import numpy as np
import soundfile as sf
from fastapi import HTTPException

from backend.utils.audio.pitch_detector import detect_pitch
from backend.utils.audio.note_mapper import freq_to_sargam, note_to_freq
from backend.utils.audio.note_segmenter import NoteSegmenter
from backend.utils.audio.techniques import detect_techniques
from backend.utils.dtw.aligner import dtw_align
from backend.utils.dtw.aligner import estimate_transposition_shift
from backend.utils.evaluation.scorer import evaluate

logger = logging.getLogger(__name__)

HOP_SIZE = 512
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
FIRST_NOTE_MAX_DEVIATION_CENTS = 140.0

SUPPORTED_CONTENT_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/aac",
    "audio/ogg",
    "audio/flac",
    "audio/webm",
    "application/octet-stream",
}

SUPPORTED_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".mpeg",
    ".mpga",
    ".m4a",
    ".aac",
    ".ogg",
    ".flac",
    ".webm",
    ".mp4",
    ".wma",
}


def _guess_suffix(upload_file) -> str:
    name = (getattr(upload_file, "filename", None) or "").strip().lower()
    suffix = os.path.splitext(name)[1]
    return suffix if suffix else ".wav"


def _decode_and_convert_to_wav(contents: bytes, source_suffix: str) -> Tuple[np.ndarray, int]:
    """Decode uploaded audio and normalize it by converting to WAV first.

    Conversion path:
    1) Try direct decode with soundfile
    2) Fallback to pydub/ffmpeg for compressed formats (mp3/m4a/etc.)
    3) Write decoded samples to temporary WAV
    4) Read WAV back for downstream processing
    """
    source_path = None
    wav_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=source_suffix) as src:
            src.write(contents)
            source_path = src.name

        try:
            decoded, samplerate = sf.read(source_path, dtype="float32")
        except Exception:
            try:
                from pydub import AudioSegment  # type: ignore
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Unsupported audio format. Install pydub + ffmpeg for mp3/m4a support, "
                        "or upload WAV/FLAC/OGG."
                    ),
                )

            try:
                segment = AudioSegment.from_file(source_path)
                segment = segment.set_channels(1)

                samplerate = int(segment.frame_rate)
                raw = np.array(segment.get_array_of_samples()).astype(np.float32)
                scale = float(1 << (8 * segment.sample_width - 1))
                decoded = raw / max(scale, 1.0)
            except Exception:
                logger.exception("Compressed audio decode failed")
                raise HTTPException(status_code=400, detail="Unsupported or corrupted audio file")

        if len(decoded.shape) > 1:
            decoded = np.mean(decoded, axis=1)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wav_tmp:
            wav_path = wav_tmp.name

        sf.write(wav_path, decoded, samplerate, subtype="PCM_16")

        wav_data, wav_samplerate = sf.read(wav_path, dtype="float32")
        if len(wav_data.shape) > 1:
            wav_data = np.mean(wav_data, axis=1)

        return wav_data, int(wav_samplerate)

    finally:
        if source_path and os.path.exists(source_path):
            os.remove(source_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


async def process_audio_core(
    upload_file,
    reference: List[Dict[str, Any]],
    conf_threshold: float = 0.8,
    debug: bool = False,
) -> Tuple[float, Dict[str, Any], List[Dict[str, Any]], Dict[str, Any], List[Tuple[int, int]], List[Dict[str, Any]]]:
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
    source_suffix = _guess_suffix(upload_file)
    content_type = (getattr(upload_file, "content_type", None) or "").lower()

    if (
        content_type
        and content_type not in SUPPORTED_CONTENT_TYPES
        and source_suffix not in SUPPORTED_EXTENSIONS
    ):
        logger.warning(
            "Unrecognized upload type received. Proceeding with decode attempt. "
            "content_type=%s suffix=%s",
            content_type,
            source_suffix,
        )

    contents = await upload_file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    # ==========================================
    # Step 2: Decode and convert to WAV internally
    # ==========================================
    try:
        data, samplerate = _decode_and_convert_to_wav(contents, source_suffix)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Audio decode/convert failed")
        raise HTTPException(status_code=500, detail="Audio file read failed")

    # ==========================================
    # Step 3: Pitch Detection & Segmentation
    # ==========================================
    try:
        reference_freqs = [
            note_to_freq(item.get("note"))
            for item in reference
            if isinstance(item, dict)
        ]
        reference_freqs = [freq for freq in reference_freqs if isinstance(freq, (int, float)) and freq > 0]
        expected_first_freq = note_to_freq(reference[0].get("note")) if reference else None

        reference_min = min(reference_freqs) if reference_freqs else None
        reference_max = max(reference_freqs) if reference_freqs else None

        def normalize_frequency_to_reference_range(freq_value: float) -> float:
            if (
                freq_value <= 0
                or reference_min is None
                or reference_max is None
            ):
                return freq_value

            lower_bound = reference_min * 0.8
            upper_bound = reference_max * 1.2

            adjusted = freq_value
            for _ in range(4):
                if adjusted < lower_bound:
                    adjusted *= 2.0
                elif adjusted > upper_bound:
                    adjusted /= 2.0
                else:
                    break

            return adjusted

        segmenter = NoteSegmenter()
        current_time = 0.0

        # store raw pitch contour per frame for technique detection
        pitch_contour = []

        for i in range(0, len(data), HOP_SIZE):
            frame = data[i : i + HOP_SIZE].astype(np.float32)
            # pad final partial frame so pitch detector gets consistent size
            if frame.shape[0] < HOP_SIZE:
                frame = np.pad(frame, (0, HOP_SIZE - frame.shape[0]), mode="constant")

            freq, conf = detect_pitch(frame, samplerate=samplerate)

            if freq and freq > 0:
                freq = normalize_frequency_to_reference_range(float(freq))

            if (
                freq and freq > 0
                and segmenter.confirmed_note is None
                and isinstance(expected_first_freq, (int, float))
                and expected_first_freq > 0
            ):
                deviation_cents = 1200.0 * math.log2(freq / expected_first_freq)
                if abs(deviation_cents) > FIRST_NOTE_MAX_DEVIATION_CENTS:
                    current_time += HOP_SIZE / samplerate
                    continue

            # record available pitch info (freq>0) regardless of segmentation confidence
            if freq and freq > 0:
                pitch_contour.append({"freq": float(freq), "time": float(current_time), "conf": float(conf)})

            # Skip frames with no pitch
            if freq <= 0:
                current_time += HOP_SIZE / samplerate
                continue

            # Skip low-confidence frames for segmentation only (configurable)
            if conf < conf_threshold:
                current_time += HOP_SIZE / samplerate
                continue

            note, cents = freq_to_sargam(freq)

            # Accept notes within Â±50 cents (half-step tolerance)
            if note and cents is not None and abs(cents) <= 50:
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
        result["dtw_transposition_shift_semitones"] = estimate_transposition_shift(reference, played)
        
        # Convert alignment (ref_note, played_note) tuples to (played_idx, ref_idx) indices
        # Use robust matching by time (with tolerance) rather than relying on object identity
        alignment_indices = []

        def _find_index_by_time(notes_list, target_note, tol=0.25):
            # try direct identity/equality first
            for idx, n in enumerate(notes_list):
                if n is target_note:
                    return idx
            # then try matching by time field within tolerance
            t = None
            try:
                t = float(target_note.get("time", None))
            except Exception:
                t = None
            if t is not None:
                best = None
                best_diff = None
                for idx, n in enumerate(notes_list):
                    try:
                        nt = float(n.get("time", 0.0))
                    except Exception:
                        continue
                    diff = abs(nt - t)
                    if best is None or diff < best_diff:
                        best = idx
                        best_diff = diff
                if best is not None and best_diff is not None and best_diff <= tol:
                    return best
            # fallback: try matching by note name + approximate time
            target_name = target_note.get("note") if isinstance(target_note, dict) else None
            if target_name:
                for idx, n in enumerate(notes_list):
                    if n.get("note") == target_name:
                        return idx
            return None

        for ref_note, played_note in alignment:
            ref_idx = _find_index_by_time(reference, ref_note)
            played_idx = _find_index_by_time(played, played_note)
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

    # Return pitch_contour as additional debug data (last element)
    return cost, result, played, techniques, alignment_indices, pitch_contour

