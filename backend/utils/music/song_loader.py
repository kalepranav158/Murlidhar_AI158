import json


def infer_content_type(song_data: dict, content_id: str | None = None) -> str:
    declared = song_data.get("type") if isinstance(song_data, dict) else None
    if isinstance(declared, str) and declared.strip():
        normalized = declared.strip().lower()
        if normalized in {"alankar", "song", "melody"}:
            return normalized

    fallback_id = content_id or (song_data.get("id") if isinstance(song_data, dict) else None)
    if isinstance(fallback_id, str):
        lowered = fallback_id.lower()
        if lowered.startswith("alankar_"):
            return "alankar"
        if lowered.startswith("melody_"):
            return "melody"

    return "song"


def load_song(path):
    # utf-8-sig safely handles files with or without BOM.
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)
