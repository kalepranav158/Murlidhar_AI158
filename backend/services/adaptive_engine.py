from backend.services.analytics_engine import compute_analytics
from typing import Optional

from backend.models.db import save_analytics_snapshot

# for now not in use - will be integrated into practice_service after testing
# ----------------------------------------
# 1ï¸âƒ£ Adaptive Tempo
# ----------------------------------------

def compute_adaptive_tempo(base_bpm: int, composite_score: float, rhythm_index: float, plateau_flag: bool) -> int:

    if plateau_flag:
        return base_bpm + 5  # slight push to break stagnation

    if composite_score > 0.85:
        return base_bpm + 10
    elif rhythm_index < 0.6:
        return max(40, base_bpm - 10)
    else:
        return base_bpm


# ----------------------------------------
# 2ï¸âƒ£ Weakest Skill Targeting
# ----------------------------------------

def detect_weakest_area(skill_indices: dict) -> str:

    weakest = min(skill_indices, key=skill_indices.get)

    if weakest == "pitch_stability_index":
        return "Long Note Swar Sadhana"
    elif weakest == "rhythm_stability_index":
        return "Slow Metronome Alankars"
    elif weakest == "consistency_index":
        return "Controlled Repetition Drills"
    else:
        return "Balanced Practice"


# ----------------------------------------
# 3ï¸âƒ£ Main Adaptive Decision Engine
# ----------------------------------------
def generate_adaptive_plan(
    user_id: str,
    base_bpm: int = 60,
    real_bpm: Optional[float] = None,
    reference_bpm: Optional[float] = None,
    tempo_deviation: Optional[float] = None
):

    analytics = compute_analytics(user_id)

    if not analytics:
        return {
            "adaptive_enabled": False
        }

    composite_score = analytics["indices"]["composite_score"]
    rhythm_index = analytics["indices"]["rhythm_index"]
    plateau_flag = analytics["flags"]["plateau"]

    # ----------------------------------
    # Existing Analytics-Based Tempo
    # ----------------------------------

    tempo = compute_adaptive_tempo(
        base_bpm,
        composite_score,
        rhythm_index,
        plateau_flag
    )

    # ----------------------------------
    # Phase D: Real Tempo Correction
    # ----------------------------------

    tempo_feedback = "Tempo stable"
    if tempo_deviation is not None and reference_bpm is not None:

    # Ignore tiny fluctuations (human tolerance zone)
        if abs(tempo_deviation) < 3:
            tempo_feedback = "Tempo control is stable."

        else:
        # Proportional correction (30% of deviation)
            correction = int(tempo_deviation * 0.3)
  
        # Adjust toward intended tempo smoothly
            tempo = reference_bpm - correction

        # Clamp tempo within safe musical range
            tempo = max(40, min(tempo, 160))

            if tempo_deviation < 0:
                tempo_feedback = "You are dragging. Increasing tempo slightly to improve rhythmic stability."

            elif tempo_deviation > 0:
                tempo_feedback = "You are rushing. Reducing tempo to regain rhythmic control."
    # ----------------------------------
    # Weakest Skill Targeting
    # ----------------------------------

    focus_area = detect_weakest_area({
    "pitch_stability_index": analytics["indices"]["pitch_index"],
    "rhythm_stability_index": analytics["indices"]["rhythm_index"],
    "consistency_index": analytics["indices"]["consistency_index"]
})

# ----------------------------------
# Skill Targeting Injection
# ----------------------------------

    target_drill = None
    exercise_mode = None
    variation_strategy = None

    if focus_area == "Long Note Swar Sadhana":
        target_drill = "Long Tone Practice"
        exercise_mode = "Isolated Notes"
        variation_strategy = "Hold each swara for 12 seconds with tanpura drone"

    elif focus_area == "Slow Metronome Alankars":
        target_drill = "Rhythmic Alankar"
        exercise_mode = "Metronome Locked"
        variation_strategy = "Play current alankar at 80% tempo with strict beat alignment"
 
    else:
        target_drill = "Controlled Repetition Drill"
        exercise_mode = "Phrase Loop"
        variation_strategy = "Repeat phrase 5 times without tempo fluctuation"



# ----------------------------------
# Plateau Intervention System
# ----------------------------------

    if plateau_flag:

        # Only increase tempo if rhythm is reasonably stable
        if rhythm_index > 0.7:
           tempo += 5
           tempo_feedback += " Plateau detected â€” tempo slightly increased to break stagnation."

        # Override drill strategy
        exercise_mode = "Variation Shift"
        variation_strategy = (
        "Switch to reverse alankar pattern or apply tempo modulation "
        "(slow-fast-slow cycle) to break performance plateau."
    )

        target_drill = "Pattern Disruption Drill"



    return {
    "adaptive_enabled": True,
    "recommended_tempo": tempo,
    "focus_area": focus_area,
    "target_drill": target_drill,
    "exercise_mode": exercise_mode,
    "variation_strategy": variation_strategy,
    "plateau_intervention": plateau_flag,
    "tempo_feedback": tempo_feedback,
    "real_bpm": real_bpm,
    "reference_bpm": reference_bpm,
    "tempo_deviation": tempo_deviation
}





def build_snapshot(analytics: dict) -> dict:
    return {
        "average_accuracy": analytics["summary"]["average_accuracy"],
        "trend_slope": analytics["trend"]["slope"],
        "predicted_next_accuracy": analytics["prediction"]["next_accuracy"],
        "consistency_index": analytics["indices"]["consistency_index"],
        "difficulty_recommendation": analytics["trend"]["classification"],
        "trend_label": analytics["trend"]["classification"],
    }
