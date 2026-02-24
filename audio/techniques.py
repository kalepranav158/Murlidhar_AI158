import numpy as np
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# Sargam note ordering for direction inference
_NOTE_ORDER = {
    "sa": 0, "Sa": 0, "Madhya Sa": 0,
    "re": 1, "Re": 1, "Madhya Re": 1,
    "ga": 2, "Ga": 2, "Madhya Ga": 2,
    "ma": 3, "Ma": 3, "Madhya Ma": 3,
    "pa": 4, "Pa": 4, "Madhya Pa": 4,
    "dha": 5, "Dha": 5, "Madhya Dha": 5,
    "ni": 6, "Ni": 6, "Madhya Ni": 6,
}


def compute_position_score(ref_range: tuple, transition_ref_indices: tuple) -> float:
    """
    Evaluate if technique occurred at expected transition.
    
    Args:
        ref_range: (ref_start_idx, ref_end_idx) where technique was detected
        transition_ref_indices: (trans_start_idx, trans_end_idx) of expected transition
    
    Returns:
        1.0 = exact transition
        0.6 = adjacent transition (off by 1)
        0.3 = same phrase, wrong transition
        0.0 = completely wrong
    """
    if ref_range is None or transition_ref_indices is None:
        return 0.0
    
    tech_start, tech_end = ref_range
    trans_start, trans_end = transition_ref_indices
    
    # Check if technique overlaps transition
    if tech_start <= trans_end and tech_end >= trans_start:
        return 1.0
    
    # Adjacent (off by 1)
    if abs(tech_start - trans_start) <= 1 or abs(tech_end - trans_end) <= 1:
        return 0.6
    
    # Same general area but wrong transition
    return 0.3


def compute_direction_score(detected_direction: str, expected_direction: str) -> float:
    """
    Evaluate if meend direction matches transition direction.
    
    Args:
        detected_direction: "up" or "down" from meend
        expected_direction: "up" or "down" from note ordering
    
    Returns:
        1.0 = match
        0.0 = mismatch
        0.8 = unknown expectation
    """
    if expected_direction is None:
        return 0.8  # Can't validate, partial credit
    
    return 1.0 if detected_direction == expected_direction else 0.0


def compute_strength_score_meend(detected_cents: float, expected_cents: float) -> float:
    """
    Evaluate meend strength (amplitude).
    
    Args:
        detected_cents: Actual pitch change in cents
        expected_cents: Expected pitch change (note interval)
    
    Returns:
        Ratio of achieved vs expected, clamped to [0, 1]
    """
    if expected_cents == 0:
        return 0.0
    
    ratio = abs(detected_cents) / abs(expected_cents)
    return min(1.0, ratio)


def compute_strength_score_gamak(oscillations: int, amplitude_cents: float) -> float:
    """
    Evaluate gamak strength (oscillations and amplitude).
    
    Args:
        oscillations: Number of oscillations detected
        amplitude_cents: Peak-to-peak amplitude
    
    Returns:
        Score based on oscillation count (expecting 4-8 is good)
    """
    # Expected oscillations: 4-8
    # If less than 4, score = osc/4; if more, score = min(1.0, 8/osc)
    if oscillations < 4:
        return oscillations / 4.0
    elif oscillations <= 8:
        return 1.0
    else:
        # More than 8 is over-oscillation; fractionally reduce
        return 8.0 / oscillations


def compute_clarity_score(detected_confidence: float) -> float:
    """
    Evaluate detection clarity (execution quality).
    
    Args:
        detected_confidence: Confidence value from detector (0-1)
    
    Returns:
        Confidence as-is
    """
    return float(detected_confidence) if detected_confidence else 0.5


def compute_note_interval_cents(from_note: str, to_note: str) -> float:
    """
    Compute expected pitch interval in cents from note names.
    
    Args:
        from_note: Starting sargam note (e.g., "Madhya Re")
        to_note: Ending sargam note (e.g., "Madhya Ga")
    
    Returns:
        Interval in cents (positive for ascending)
    """
    # Sargam intervals in cents (12-tone equal temperament approximation)
    intervals = {
        ("sa", "re"): 200,    ("re", "ga"): 200,    ("ga", "ma"): 100,
        ("ma", "pa"): 200,    ("pa", "dha"): 200,   ("dha", "ni"): 200,
        ("ni", "sa"): 100,
        # Reverse intervals
        ("re", "sa"): -200,   ("ga", "re"): -200,   ("ma", "ga"): -100,
        ("pa", "ma"): -200,   ("dha", "pa"): -200,  ("ni", "dha"): -200,
        ("sa", "ni"): -100,
    }
    
    # Normalize note names
    from_norm = from_note.lower().strip().replace("madhya ", "").replace("taar ", "")
    to_norm = to_note.lower().strip().replace("madhya ", "").replace("taar ", "")
    
    return intervals.get((from_norm, to_norm), 200.0)  # Default: 200 cents


def _score_transitions_expressive(detected: Dict[str, Any], transitions: list, details: Dict[str, Any], played_notes: List[Dict[str, Any]] = None, alignment_indices: List[tuple] = None) -> Dict[str, Any]:
    """
    Score techniques with 4-dimensional expressive model:
    
    1. Position Score (0.4 weight): Did technique occur at expected transition?
    2. Direction Score (0.2 weight): Does meend direction match musical direction?
    3. Strength Score (0.25 weight): Is amplitude/oscillation count appropriate?
    4. Clarity Score (0.15 weight): How confident is the detection?
    
    Returns continuous score reflecting musical quality, not binary match.
    """
    if not transitions:
        return {"technique_score": 0.0, "details": details}

    expected_techniques = [t for t in transitions if t.get("technique")]
    if not expected_techniques:
        return {"technique_score": 0.0, "details": details}

    details["expected_transitions"] = expected_techniques
    
    use_alignment = alignment_indices and played_notes and len(alignment_indices) > 0
    
    total_score = 0.0

    for trans_idx, trans in enumerate(expected_techniques):
        tech_type = trans.get("technique")
        
        # For position score, we need transition boundaries in reference space
        trans_start_time = float(trans.get("from_time", 0.0))
        trans_end_time = float(trans.get("to_time", 0.0))
        
        from_note = trans.get("from", "")
        to_note = trans.get("to", "")
        expected_direction = _infer_direction(from_note, to_note)
        expected_cents = compute_note_interval_cents(from_note, to_note)
        
        best_transition_score = 0.0
        best_match = None

        if tech_type == "meend":
            meends = detected.get("meend", [])
            
            for meend in meends:
                m_dir = meend.get("direction", "up")
                m_cents = meend.get("cents_change", 0.0)
                m_conf = meend.get("confidence", 0.5)
                
                # Compute position score
                position_score = 0.0
                if use_alignment:
                    ref_range = map_technique_to_reference(meend, played_notes, alignment_indices)
                    if ref_range:
                        # Map transition times to reference indices (simplified: use indices 0-based)
                        # In reality, we'd need to map from_time/to_time to their reference note indices
                        position_score = compute_position_score(ref_range, (trans_idx, trans_idx + 1))
                else:
                    # Time-based position: if meend overlaps transition, score 1.0
                    m_start = meend.get("start_time", 0.0)
                    m_end = meend.get("end_time", 0.0)
                    if m_start <= trans_end_time and m_end >= trans_start_time:
                        position_score = 1.0
                    else:
                        position_score = 0.3  # Wrong region
                
                # Compute direction score
                direction_score = compute_direction_score(m_dir, expected_direction)
                
                # Compute strength score
                strength_score = compute_strength_score_meend(m_cents, expected_cents)
                
                # Compute clarity score
                clarity_score = compute_clarity_score(m_conf)
                
                # Position gates the score; other dimensions are weighted within
                transition_score = position_score * (
                    0.4 * direction_score +
                    0.35 * strength_score +
                    0.25 * clarity_score
                )
                
                if transition_score > best_transition_score:
                    best_transition_score = transition_score
                    best_match = {
                        "transition": trans,
                        "meend": meend,
                        "position_score": round(position_score, 3),
                        "direction_score": round(direction_score, 3),
                        "strength_score": round(strength_score, 3),
                        "clarity_score": round(clarity_score, 3),
                        "composite_score": round(transition_score, 3)
                    }
        
        elif tech_type == "gamak":
            gamaks = detected.get("gamak", [])
            
            for gamak in gamaks:
                g_osc = gamak.get("oscillations", 0)
                g_amp = gamak.get("amplitude_cents", 0.0)
                g_conf = gamak.get("confidence", 0.5)
                
                # Compute position score
                position_score = 0.0
                if use_alignment:
                    ref_range = map_technique_to_reference(gamak, played_notes, alignment_indices)
                    if ref_range:
                        position_score = compute_position_score(ref_range, (trans_idx, trans_idx + 1))
                else:
                    # Time-based position
                    g_start = gamak.get("start_time", 0.0)
                    g_end = gamak.get("end_time", 0.0)
                    if g_start <= trans_end_time and g_end >= trans_start_time:
                        position_score = 1.0
                    else:
                        position_score = 0.3
                
                # Direction not applicable to gamak (it's oscillatory)
                direction_score = 0.8  # No direction validation, partial credit
                
                # Strength score for gamak
                strength_score = compute_strength_score_gamak(g_osc, g_amp)
                
                # Clarity score
                clarity_score = compute_clarity_score(g_conf)
                
                # Position gates the score; other dimensions are weighted within
                transition_score = position_score * (
                    0.4 * direction_score +
                    0.35 * strength_score +
                    0.25 * clarity_score
                )
                
                if transition_score > best_transition_score:
                    best_transition_score = transition_score
                    best_match = {
                        "transition": trans,
                        "gamak": gamak,
                        "position_score": round(position_score, 3),
                        "direction_score": round(direction_score, 3),
                        "strength_score": round(strength_score, 3),
                        "clarity_score": round(clarity_score, 3),
                        "composite_score": round(transition_score, 3)
                    }
        
        if best_match:
            details["found_transitions"].append(best_match)
        
        # Add best_score to total (normalized by number of transitions at end)
        total_score += best_transition_score
    
    # Final technique score: average of per-transition scores
    final_score = total_score / len(expected_techniques) if expected_techniques else 0.0
    
    return {"technique_score": round(final_score, 3), "details": details}


def map_technique_to_reference(tech_segment: Dict[str, Any], played_notes: List[Dict[str, Any]], alignment_indices: List[tuple]) -> Optional[tuple]:
    """
    Map a detected technique (time-based) to reference note indices via DTW alignment.
    
    Args:
        tech_segment: Detected technique dict with start_time, end_time
        played_notes: List of played note dicts with time field
        alignment_indices: DTW path as [(played_idx, ref_idx), ...]
    
    Returns:
        (ref_start_idx, ref_end_idx) or None if no mapping found
    """
    if not alignment_indices:
        return None
    
    start_t = tech_segment.get("start_time", 0.0)
    end_t = tech_segment.get("end_time", 0.0)
    
    # Find played note indices that fall within technique time window
    affected_played_indices = set()
    for i, note in enumerate(played_notes):
        note_time = note.get("time", 0.0)
        if start_t <= note_time <= end_t:
            affected_played_indices.add(i)
    
    if not affected_played_indices:
        return None
    
    # Map to reference indices via DTW path
    ref_indices = []
    for played_idx, ref_idx in alignment_indices:
        if played_idx in affected_played_indices:
            ref_indices.append(ref_idx)
    
    if not ref_indices:
        return None
    
    return min(ref_indices), max(ref_indices)


def _infer_direction(from_note: str, to_note: str) -> str:
    """
    Infer transition direction from note names.
    
    Returns: "up", "down", or None if uncertain
    """
    if not from_note or not to_note:
        return None
    
    from_idx = _NOTE_ORDER.get(from_note)
    to_idx = _NOTE_ORDER.get(to_note)
    
    if from_idx is None or to_idx is None:
        return None
    
    if to_idx > from_idx:
        return "up"
    elif to_idx < from_idx:
        return "down"
    else:
        return None  # Same note


def _detect_gamak(times: np.ndarray, logcents: np.ndarray) -> List[Dict[str, Any]]:
    """
    Detect gamak segments (rapid oscillations) from smoothed log-cent contour.
    
    Gamak characteristics:
    - Multiple sign changes (≥4 oscillations)
    - High amplitude (≥30 cents)
    - Short duration (≤0.6 sec)
    - Small net pitch change (≤80 cents)
    """
    MIN_OSCILLATIONS = 4
    MIN_AMPLITUDE = 50.0      # cents (vibrato <25, gamak >40; 50 filters vibrato, preserves gamak)
    MAX_DURATION = 0.6        # seconds
    MAX_NET_CHANGE = 80.0     # cents

    if len(logcents) < 3:
        return []

    diffs = np.diff(logcents)
    signs = np.sign(diffs)

    gamaks = []
    start = 0

    for i in range(1, len(signs)):
        # Detect sign change (oscillation)
        if signs[i] != signs[i - 1] and signs[i] != 0:
            end = i
            duration = float(times[end] - times[start])
            segment = logcents[start:end]

            if len(segment) < 3:
                start = i
                continue

            amplitude = float(np.max(segment) - np.min(segment))
            net_change = float(abs(segment[-1] - segment[0]))

            # Count zero crossings (oscillations)
            sign_changes = np.diff(np.sign(diffs[start:end]))
            osc_count = int(np.sum(sign_changes != 0))
            
            # Stability anchor: oscillation should be centered around stable note, not drift
            # Check if mean value of first half vs second half drifts significantly
            mid = len(segment) // 2
            if mid > 0:
                first_half_mean = float(np.mean(segment[:mid]))
                second_half_mean = float(np.mean(segment[mid:]))
                center_drift = abs(first_half_mean - second_half_mean)
            else:
                center_drift = 0.0
            
            MAX_CENTER_DRIFT = 100.0  # cents; oscillation should stay centered

            if (
                osc_count >= MIN_OSCILLATIONS
                and amplitude >= MIN_AMPLITUDE
                and duration <= MAX_DURATION
                and net_change <= MAX_NET_CHANGE
                and center_drift <= MAX_CENTER_DRIFT
            ):
                gamaks.append({
                    "start_time": float(times[start]),
                    "end_time": float(times[end]),
                    "amplitude_cents": amplitude,
                    "oscillations": osc_count,
                    "net_change": net_change,
                    "confidence": min(1.0, float(osc_count) / 8.0),
                })

            start = i

    return gamaks


def _savgol_smooth(freqs: np.ndarray) -> np.ndarray:
    """Apply Savitzky–Golay smoothing if SciPy is available.

    Falls back to raw input if SciPy is not installed or window too small.
    """
    try:
        from scipy.signal import savgol_filter
    except Exception:
        logger.warning("scipy not available; skipping smoothing")
        return freqs

    n = len(freqs)
    if n < 5:
        return freqs

    # choose odd window length <= n
    win = 11
    if win > n:
        win = n if n % 2 == 1 else n - 1
    poly = 2
    try:
        return savgol_filter(freqs, win, poly)
    except Exception:
        logger.exception("savgol_filter failed; returning raw freqs")
        return freqs


def detect_techniques(pitch_contour: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect expressive techniques from a frame-level pitch contour.

    Algorithm (Meend):
    1) Smooth frequency contour with Savitzky–Golay
    2) Convert to cents and compute per-frame diffs
    3) Find contiguous monotonic runs (segment-based)
    4) Validate each segment (duration, cents change, monotonic proportion)
    5) Merge nearby detections (min gap rule)
    """

    # Hard boundaries for flute (Hz)
    MIN_FREQ = 80.0      
    MAX_FREQ = 1500.0    
    MIN_CONF = 0.85      # confidence gating
    MAX_CENTS_CHANGE = 600.0  # outlier clamp

    # Filter valid positive frequencies within bounds and confidence threshold
    times = []
    freqs = []
    confs = []
    for p in pitch_contour:
        f = p.get("freq", 0)
        c = p.get("conf", 1.0)
        if f and MIN_FREQ <= f <= MAX_FREQ and c >= MIN_CONF:
            times.append(float(p.get("time", 0.0)))
            freqs.append(float(f))
            confs.append(float(c))

    if len(freqs) < 2:
        return {"meend": []}

    times = np.array(times)
    freqs = np.array(freqs)

    # 1) smoothing
    smoothed = _savgol_smooth(freqs)

    # 2) convert to log-cents
    with np.errstate(divide='ignore'):
        logcents = 1200.0 * np.log2(smoothed)

    # 3) per-frame diffs in cents
    diffs = np.diff(logcents)

    # detection thresholds
    MIN_CENTS_TOTAL = 100.0   # > ~1 semitone
    MIN_DURATION = 0.15       # seconds
    MIN_MONOTONIC_PROP = 0.8
    SMALL_DIFF_THRESHOLD = 0.5  # cents per-frame to ignore micro-jitter
    MERGE_GAP = 0.1            # 100 ms

    n = len(logcents)
    signs = np.zeros_like(diffs)
    signs[np.abs(diffs) >= SMALL_DIFF_THRESHOLD] = np.sign(diffs[np.abs(diffs) >= SMALL_DIFF_THRESHOLD])

    meends = []

    # 4) Find contiguous monotonic segments
    start = None
    current_sign = 0
    for i in range(len(signs)):
        s = int(signs[i])
        if s == 0:
            # jitter / flat region
            if start is not None:
                end_idx = i  # end at i
                # validate segment start..end_idx
                a = start
                b = end_idx
                duration = float(times[b] - times[a])
                total_change = float(logcents[b] - logcents[a])
                if duration >= MIN_DURATION and abs(total_change) >= MIN_CENTS_TOTAL:
                    # proportion of diffs matching direction
                    window_diffs = diffs[a:b]
                    if window_diffs.size > 0:
                        # Only count diffs that exceed micro-jitter threshold
                        valid_mask = np.abs(window_diffs) >= SMALL_DIFF_THRESHOLD
                        valid_diffs = window_diffs[valid_mask]
                        if valid_diffs.size > 0:
                            prop = float(np.mean(np.sign(valid_diffs) == current_sign))
                        else:
                            prop = 1.0  # All diffs were jitter; treat as monotonic
                        if prop >= MIN_MONOTONIC_PROP and abs(total_change) <= MAX_CENTS_CHANGE:
                            meends.append({
                                "start_time": float(times[a]),
                                "end_time": float(times[b]),
                                "cents_change": float(total_change),
                                "direction": "up" if total_change > 0 else "down",
                                "confidence": prop,
                            })
            start = None
            current_sign = 0
            continue

        # s is non-zero
        if start is None:
            # begin a new potential segment at frame i
            start = i
            current_sign = s
            continue

        # if sign continues, keep going
        if s == current_sign:
            continue

        # sign flipped -> end segment at i
        end_idx = i
        a = start
        b = end_idx
        duration = float(times[b] - times[a])
        total_change = float(logcents[b] - logcents[a])
        if duration >= MIN_DURATION and abs(total_change) >= MIN_CENTS_TOTAL:
            window_diffs = diffs[a:b]
            if window_diffs.size > 0:
                valid_mask = np.abs(window_diffs) >= SMALL_DIFF_THRESHOLD
                valid_diffs = window_diffs[valid_mask]
                if valid_diffs.size > 0:
                    prop = float(np.mean(np.sign(valid_diffs) == current_sign))
                else:
                    prop = 1.0
                if prop >= MIN_MONOTONIC_PROP and abs(total_change) <= MAX_CENTS_CHANGE:
                    meends.append({
                        "start_time": float(times[a]),
                        "end_time": float(times[b]),
                        "cents_change": float(total_change),
                        "direction": "up" if total_change > 0 else "down",
                        "confidence": prop,
                    })
        # start new candidate
        start = i
        current_sign = s

    # if ending while open
    if start is not None and start < n - 1:
        a = start
        b = n - 1
        duration = float(times[b] - times[a])
        total_change = float(logcents[b] - logcents[a])
        if duration >= MIN_DURATION and abs(total_change) >= MIN_CENTS_TOTAL:
            window_diffs = diffs[a:b]
            if window_diffs.size > 0:
                valid_mask = np.abs(window_diffs) >= SMALL_DIFF_THRESHOLD
                valid_diffs = window_diffs[valid_mask]
                if valid_diffs.size > 0:
                    prop = float(np.mean(np.sign(valid_diffs) == current_sign))
                else:
                    prop = 1.0
                if prop >= MIN_MONOTONIC_PROP and abs(total_change) <= MAX_CENTS_CHANGE:
                    meends.append({
                        "start_time": float(times[a]),
                        "end_time": float(times[b]),
                        "cents_change": float(total_change),
                        "direction": "up" if total_change > 0 else "down",
                        "confidence": prop,
                    })

    # 5) merge nearby detections (minimum gap rule)
    if not meends:
        meends = []

    meends_sorted = sorted(meends, key=lambda x: x["start_time"])
    merged = [meends_sorted[0]] if meends_sorted else []
    for m in meends_sorted[1:]:
        prev = merged[-1]
        gap = m["start_time"] - prev["end_time"]
        if gap < MERGE_GAP:
            # merge
            prev_end = max(prev["end_time"], m["end_time"])
            prev_change = prev["cents_change"] + m["cents_change"]
            prev_conf = float((prev.get("confidence", 0.0) + m.get("confidence", 0.0)) / 2.0)
            prev["end_time"] = prev_end
            prev["cents_change"] = prev_change
            prev["confidence"] = prev_conf
            prev["direction"] = "up" if prev_change > 0 else "down"
        else:
            merged.append(m)

    # 6) Detect gamak (rapid oscillations)
    gamaks = _detect_gamak(times, logcents)

    return {"meend": merged, "gamak": gamaks}


def compare_with_reference(detected: Dict[str, Any], reference_phrase: Dict[str, Any], played_notes: List[Dict[str, Any]] = None, alignment_indices: List[tuple] = None) -> Dict[str, Any]:
    """
    Compare detected techniques with reference phrase via expressive 4-dimensional scoring:
    
    1. Position Score (40%): Correct transition?
    2. Direction Score (20%): Correct direction (meend)?
    3. Strength Score (25%): Appropriate amplitude/oscillations?
    4. Clarity Score (15%): Detection confidence?

    Returns continuous score reflecting musical refinement, not binary match.

    Output:
      {"technique_score": float(0..1), "details": { scoring breakdown } }
    """

    if not reference_phrase:
        return {"technique_score": 0.0, "details": {}}

    details = {"expected_transitions": [], "found_transitions": [], "meends": detected.get("meend", []), "gamaks": detected.get("gamak", [])}

    # Try new transition-based format first
    transitions = reference_phrase.get("transitions", [])
    
    if transitions:
        # Transition-based validation with expressive scoring
        return _score_transitions_expressive(detected, transitions, details, played_notes, alignment_indices)
    else:
        # Fallback to old phrase-based format for backward compatibility
        return _score_phrase_overlap(detected, reference_phrase, details)


def _score_transitions(detected: Dict[str, Any], transitions: list, details: Dict[str, Any], played_notes: List[Dict[str, Any]] = None, alignment_indices: List[tuple] = None) -> Dict[str, Any]:
    """
    Score detected techniques against explicit transitions.
    
    If alignment_indices provided (DTW path):
      - Map technique time window to reference note indices
      - Validate technique overlaps expected transition in reference space
    
    Otherwise (no alignment):
      - Use time-based overlap with transition window (backward compatible)
    """
    meends = detected.get("meend", [])
    
    if not transitions:
        return {"technique_score": 0.0, "details": details}

    expected_techniques = [t for t in transitions if t.get("technique")]
    if not expected_techniques:
        return {"technique_score": 0.0, "details": details}

    details["expected_transitions"] = expected_techniques

    total_score = 0.0
    score_per_transition = 1.0 / len(expected_techniques)

    # Determine if we can use alignment-based validation
    use_alignment = alignment_indices and played_notes and len(alignment_indices) > 0

    for trans in expected_techniques:
        tech = trans.get("technique")
        trans_start = float(trans.get("from_time", 0.0))
        trans_end = float(trans.get("to_time", 0.0))
        trans_dur = max(0.001, trans_end - trans_start)

        # Infer expected direction from note names
        from_note = trans.get("from", "")
        to_note = trans.get("to", "")
        expected_direction = _infer_direction(from_note, to_note)

        if tech == "meend":
            matched = False
            for meend in meends:
                m_start = meend.get("start_time", 0.0)
                m_end = meend.get("end_time", 0.0)
                m_dir = meend.get("direction", "up")

                # Use alignment-based validation if available
                if use_alignment:
                    ref_range = map_technique_to_reference(meend, played_notes, alignment_indices)
                    if ref_range:
                        # Map transition from_time/to_time to reference note indices
                        # to determine which reference notes define this transition
                        from_time_idx = next((i for i, n in enumerate(trans.get("from_notes", [])) if n.get("time", 0) >= trans_start), 0)
                        to_time_idx = next((i for i, n in enumerate(trans.get("to_notes", [])) if n.get("time", 0) <= trans_end), len(trans.get("to_notes", [])))
                        
                        # Actually, we need to find which reference indices correspond to from_note and to_note
                        # For now, use a simpler heuristic: if meend's reference range overlaps with transition
                        ref_start, ref_end = ref_range
                        
                        # Find which transition notes these indices correspond to
                        # This requires knowing the note boundaries in the reference
                        # For MVP, fall back to time-based if alignment-based is complex
                        if ref_start <= ref_end:  # Valid range found
                            # Assume transition involves these reference indices
                            matched = True
                            details["found_transitions"].append({
                                "transition": trans,
                                "meend": meend,
                                "alignment_validated": True,
                                "ref_index_range": (ref_start, ref_end),
                                "expected_direction": expected_direction,
                                "detected_direction": m_dir,
                                "direction_match": m_dir == expected_direction if expected_direction else "unknown"
                            })
                            break
                
                # Fallback to time-based validation (always works)
                if not matched:
                    # Check overlap with transition window (relaxed to 30%)
                    overlap_start = max(trans_start, m_start)
                    overlap_end = min(trans_end, m_end)
                    overlap = max(0.0, overlap_end - overlap_start)

                    # Require ≥30% overlap of transition window
                    overlap_ratio = overlap / trans_dur if trans_dur > 0 else 0.0
                    
                    if overlap_ratio >= 0.3:
                        # Validate direction if expected_direction is known
                        if expected_direction is not None and m_dir != expected_direction:
                            # Direction mismatch — skip this meend
                            continue
                        
                        # Meend overlaps ≥30% of transition window and direction matches
                        matched = True
                        details["found_transitions"].append({
                            "transition": trans,
                            "meend": meend,
                            "overlap_ratio": round(overlap_ratio, 3),
                            "expected_direction": expected_direction,
                            "detected_direction": m_dir,
                            "direction_match": m_dir == expected_direction if expected_direction else "unknown"
                        })
                        break

            if matched:
                total_score += score_per_transition

        elif tech == "gamak":
            # Gamak detection (rapid oscillation around note)
            gamaks = detected.get("gamak", [])
            matched = False
            for gamak in gamaks:
                g_start = gamak.get("start_time", 0.0)
                g_end = gamak.get("end_time", 0.0)

                # Use alignment-based validation if available
                if use_alignment:
                    ref_range = map_technique_to_reference(gamak, played_notes, alignment_indices)
                    if ref_range and ref_range[0] <= ref_range[1]:
                        matched = True
                        details["found_transitions"].append({
                            "transition": trans,
                            "gamak": gamak,
                            "alignment_validated": True,
                            "ref_index_range": ref_range,
                            "amplitude_cents": round(gamak.get("amplitude_cents", 0.0), 1),
                            "oscillations": gamak.get("oscillations", 0)
                        })
                        break
                
                # Fallback to time-based validation
                if not matched:
                    # Check overlap with transition window (same 30% threshold)
                    overlap_start = max(trans_start, g_start)
                    overlap_end = min(trans_end, g_end)
                    overlap = max(0.0, overlap_end - overlap_start)

                    overlap_ratio = overlap / trans_dur if trans_dur > 0 else 0.0

                    if overlap_ratio >= 0.3:
                        # Gamak overlaps ≥30% of transition window
                        matched = True
                        details["found_transitions"].append({
                            "transition": trans,
                            "gamak": gamak,
                            "overlap_ratio": round(overlap_ratio, 3),
                            "amplitude_cents": round(gamak.get("amplitude_cents", 0.0), 1),
                            "oscillations": gamak.get("oscillations", 0)
                        })
                        break

            if matched:
                total_score += score_per_transition

    return {"technique_score": round(total_score, 3), "details": details}


def _score_transitions(detected: Dict[str, Any], transitions: list, details: Dict[str, Any], played_notes: List[Dict[str, Any]] = None, alignment_indices: List[tuple] = None) -> Dict[str, Any]:
    """
    DEPRECATED: Use _score_transitions_expressive instead.
    This function is kept for backward compatibility but delegates to the expressive model.
    """
    return _score_transitions_expressive(detected, transitions, details, played_notes, alignment_indices)


def _score_phrase_overlap(detected: Dict[str, Any], reference_phrase: Dict[str, Any], details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback: phrase-level overlap scoring (backward compatible with old format).
    """
    expected = []
    if "techniques" in reference_phrase:
        expected = reference_phrase.get("techniques") or []
    elif "technique" in reference_phrase:
        expected = [reference_phrase.get("technique")]

    expected = [e for e in expected if e]

    if not expected:
        return {"technique_score": 0.0, "details": details}

    details["expected"] = expected

    score_per_tech = 1.0 / len(expected)
    total_score = 0.0

    # Determine phrase time window from reference notes
    notes = reference_phrase.get("notes", [])
    if not notes:
        return {"technique_score": 0.0, "details": details}

    note_times = []
    for note in notes:
        t = note.get("time")
        if t is not None:
            note_times.append(float(t))

    if not note_times:
        return {"technique_score": 0.0, "details": details}

    start_t = float(min(note_times))
    end_t = float(max(note_times))
    phrase_dur = max(0.001, end_t - start_t)

    meends = detected.get("meend", [])
    for tech in expected:
        if tech == "meend":
            matched = False
            for m in meends:
                a1, b1 = start_t, end_t
                a2, b2 = m.get("start_time", 0.0), m.get("end_time", 0.0)
                overlap_start = max(a1, a2)
                overlap_end = min(b1, b2)
                inter = max(0.0, overlap_end - overlap_start)
                if phrase_dur > 0 and inter / phrase_dur >= 0.5:
                    matched = True
                    break
            if matched:
                total_score += score_per_tech
        elif tech == "gamak":
            gamaks = detected.get("gamak", [])
            matched = False
            for g in gamaks:
                a1, b1 = start_t, end_t
                a2, b2 = g.get("start_time", 0.0), g.get("end_time", 0.0)
                overlap_start = max(a1, a2)
                overlap_end = min(b1, b2)
                inter = max(0.0, overlap_end - overlap_start)
                if phrase_dur > 0 and inter / phrase_dur >= 0.5:
                    matched = True
                    break
            if matched:
                total_score += score_per_tech

    return {"technique_score": round(total_score, 3), "details": details}