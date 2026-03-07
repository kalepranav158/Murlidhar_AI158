def generate_song_adaptive_plan(
    user_id: str,
    song: dict,
    phrase_index: int,
    accuracy: float,
    base_tempo: int
):

    from backend.models.db import get_weakest_phrase

    weakest = get_weakest_phrase(user_id, song["id"])

    recommended_tempo = base_tempo
    recommendation = "Continue practicing."

    # Slow down if accuracy is low
    if accuracy < 90:
        recommended_tempo = max(base_tempo - 5, 40)
        recommendation = "Slow down and stabilize this phrase."

    # If mastered, increase slightly
    elif accuracy >= 97:
        recommended_tempo = base_tempo + 5
        recommendation = "Good control. Slight tempo increase recommended."

    # If another phrase is weaker
    if weakest and weakest["phrase_id"] != phrase_index:
        recommendation = f"Focus more on phrase {weakest['phrase_id']} â€” it needs improvement."

    return {
        "adaptive_enabled": True,
        "recommended_tempo": recommended_tempo,
        "focus_phrase": weakest["phrase_id"] if weakest else phrase_index,
        "song_recommendation": recommendation
    }
