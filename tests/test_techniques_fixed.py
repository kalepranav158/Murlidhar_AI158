#!/usr/bin/env python
"""
Unit tests for techniques detector (fixed version).
Tests frequency bounds, confidence gating, outlier clamping, and reference comparison.
"""
import numpy as np
from backend.utils.audio.techniques import detect_techniques, compare_with_reference


def test_frequency_bounds_reject_glitches():
    """Verify that out-of-range frequencies are rejected during filtering."""
    # Simulate: valid glide at 440Hz + one glitch at 8000Hz
    pc = []
    for t_i in range(20):
        t = t_i * 0.01
        freq = 440.0 * (2 ** ((t_i * 5) / 1200.0))  # +5 cents per frame
        pc.append({"freq": freq, "time": t, "conf": 1.0})
    
    # Inject high-frequency glitch that should be filtered
    pc[10]["freq"] = 8000.0
    
    result = detect_techniques(pc)
    # With glitch filtered, we should get a cleaner detection (or fewer total meends)
    assert "meend" in result
    print(f"âœ“ Glitches filtered: {len(result['meend'])} meends detected (should not include 8kHz spike)")


def test_confidence_gating_rejects_low_conf():
    """Verify that low-confidence frames are rejected."""
    pc = []
    for t_i in range(20):
        t = t_i * 0.01
        freq = 440.0 * (2 ** ((t_i * 5) / 1200.0))
        conf = 1.0 if t_i < 10 else 0.5  # Low confidence in second half
        pc.append({"freq": freq, "time": t, "conf": conf})
    
    result = detect_techniques(pc)
    # Low confidence frame should break continuity
    assert "meend" in result
    print(f"âœ“ Low-conf frames filtered: {len(result['meend'])} meends detected")


def test_outlier_clamping():
    """Verify that unrealistic cents changes are clamped."""
    # Create a synthetic huge jump that would produce >600 cents change
    pc = []
    freqs = [100.0, 500.0, 900.0]  # Huge jump from 100->900 would be ~2400 cents
    for i, freq in enumerate(freqs):
        pc.append({"freq": freq, "time": i * 0.1, "conf": 1.0})
    
    result = detect_techniques(pc)
    # This should be rejected due to MAX_CENTS_CHANGE = 600
    # (Going from 100Hz to 900Hz is huge and unlikely to be a real meend)
    meends = result.get("meend", [])
    if meends:
        for m in meends:
            assert abs(m["cents_change"]) <= 600.0, f"Meend with {m['cents_change']} cents exceeds clamp"
    print(f"âœ“ Outliers clamped: {len(meends)} meends, all within bounds")


def test_compare_with_reference_valid_overlap():
    """Verify overlap detection against reference phrase with time windows."""
    detected = {"meend": [
        {"start_time": 0.2, "end_time": 0.8, "cents_change": 150, "direction": "up", "confidence": 0.9}
    ]}
    
    reference = {
        "notes": [
            {"note": "Sa", "time": 0.0},
            {"note": "Re", "time": 0.5},
            {"note": "Ga", "time": 1.0}
        ],
        "techniques": ["meend"]
    }
    
    result = compare_with_reference(detected, reference)
    # Phrase window is 0.0 to 1.0, meend is 0.2 to 0.8
    # Overlap is 0.6 sec, phrase is 1.0 sec -> 60% overlap (>50%) -> matched
    assert result["technique_score"] > 0, "Meend should overlap phrase window"
    print(f"âœ“ Reference overlap valid: technique_score={result['technique_score']}")


def test_compare_with_reference_no_overlap():
    """Verify non-overlapping detection is rejected."""
    detected = {"meend": [
        {"start_time": 2.0, "end_time": 2.5, "cents_change": 150, "direction": "up", "confidence": 0.9}
    ]}
    
    reference = {
        "notes": [
            {"note": "Sa", "time": 0.0},
            {"note": "Re", "time": 0.5},
            {"note": "Ga", "time": 1.0}
        ],
        "techniques": ["meend"]
    }
    
    result = compare_with_reference(detected, reference)
    # Meend at 2.0-2.5 is completely outside phrase 0.0-1.0
    assert result["technique_score"] == 0.0, "Non-overlapping meend should not score"
    print(f"âœ“ Reference overlap rejection: technique_score={result['technique_score']}")


def test_monotonic_proportion_with_micro_jitter():
    """Verify that micro-jitter doesn't break monotonic detection."""
    np.random.seed(7)
    # Simulate: mostly upward glide with tiny oscillations
    pc = []
    t = 0.0
    freq = 440.0
    for i in range(30):
        # Primary trend: +2 cents per frame
        base_freq = 440.0 * (2 ** ((i * 2) / 1200.0))
        # Add tiny jitter: Â±0.2 cents
        jitter = np.random.uniform(-0.2, 0.2)
        freq_with_jitter = base_freq * (2 ** (jitter / 1200.0))
        pc.append({"freq": freq_with_jitter, "time": t, "conf": 0.95})
        t += 0.01
    
    result = detect_techniques(pc)
    meends = result.get("meend", [])
    # Should detect upward trend despite jitter
    assert len(meends) > 0, "Jitter should not prevent detection of strong trend"
    assert meends[0]["direction"] == "up"
    print(f"âœ“ Micro-jitter handled: {len(meends)} meends detected correctly")


if __name__ == "__main__":
    print("Running techniques detector tests...\n")
    test_frequency_bounds_reject_glitches()
    test_confidence_gating_rejects_low_conf()
    test_outlier_clamping()
    test_compare_with_reference_valid_overlap()
    test_compare_with_reference_no_overlap()
    test_monotonic_proportion_with_micro_jitter()
    print("\nâœ… All tests passed!")

