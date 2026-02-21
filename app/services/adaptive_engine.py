from app.services.analytics_engine import compute_analytics
from typing import Optional

# for now not in use - will be integrated into practice_service after testing
# ----------------------------------------
# 1️⃣ Adaptive Tempo
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
# 2️⃣ Weakest Skill Targeting
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
# 3️⃣ Main Adaptive Decision Engine
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

        if tempo_deviation < -5:
            tempo -= 5
            tempo_feedback = "You are dragging. Stabilize rhythm at lower tempo."

        elif tempo_deviation > 5:
            tempo -= 5
            tempo_feedback = "You are rushing. Slow down to regain control."

        else:
            tempo_feedback = "Tempo control is stable."

    # Prevent negative or unrealistic tempo
    if tempo < 30:
        tempo = 30

    # ----------------------------------
    # Weakest Skill Targeting
    # ----------------------------------

    focus_area = detect_weakest_area({
        "pitch_stability_index": analytics["indices"]["pitch_index"],
        "rhythm_stability_index": analytics["indices"]["rhythm_index"],
        "consistency_index": analytics["indices"]["consistency_index"]
    })

    return {
        "adaptive_enabled": True,
        "recommended_tempo": tempo,
        "focus_area": focus_area,
        "plateau_intervention": plateau_flag,
        "tempo_feedback": tempo_feedback,
        "real_bpm": real_bpm,
        "reference_bpm": reference_bpm,
        "tempo_deviation": tempo_deviation
    }



