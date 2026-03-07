def compute_alankar_level(user_id: str, song: dict, composite_score: float | None, plateau_flag: bool):

    tempo_levels = song.get("tempo_levels", [song.get("base_tempo", 60)])

    if not tempo_levels:
        return {
            "level_index": 0,
            "recommended_tempo": song.get("base_tempo", 60)
        }

    # Default level
    level_index = 0

    # Determine progression
    if composite_score is not None:

        if composite_score >= 0.85:
            level_index = min(1, len(tempo_levels) - 1)

        if composite_score >= 0.92:
            level_index = min(2, len(tempo_levels) - 1)

    # Plateau override
    if plateau_flag:
        level_index = min(level_index + 1, len(tempo_levels) - 1)

    return {
        "level_index": level_index,
        "recommended_tempo": tempo_levels[level_index]
    }