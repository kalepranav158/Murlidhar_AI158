import os
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from music.song_loader import infer_content_type, load_song

router = APIRouter(prefix="/songs", tags=["Songs"])

SONGS_FOLDER = "songs"


@router.get("/")
def list_songs(content_type: str | None = Query(default=None)):
    normalized_filter = content_type.strip().lower() if isinstance(content_type, str) else None
    songs = []

    for file in os.listdir(SONGS_FOLDER):
        if file.endswith(".json"):
            song_id = file.replace(".json", "")
            song_path = os.path.join(SONGS_FOLDER, file)

            song_data = load_song(song_path)
            resolved_content_type = infer_content_type(song_data, song_id)

            if normalized_filter and resolved_content_type != normalized_filter:
                continue

            songs.append({
                "song_id": song_id,
                "title": song_data.get("title", song_id),
                "tempo": song_data.get("tempo", None),
                "phrases": len(song_data.get("phrases", [])),
                "content_type": resolved_content_type,
            })

    return songs


@router.get("/{song_id}/phrase/{phrase_index}")
def get_phrase_reference(song_id: str, phrase_index: int):
    song_path = os.path.join(SONGS_FOLDER, f"{song_id}.json")
    if not os.path.exists(song_path):
        raise HTTPException(status_code=404, detail="Song not found")

    song_data = load_song(song_path)
    phrases = song_data.get("phrases", [])
    if not isinstance(phrases, list) or phrase_index < 0 or phrase_index >= len(phrases):
        raise HTTPException(status_code=400, detail="Invalid phrase index")

    phrase = phrases[phrase_index] if isinstance(phrases[phrase_index], dict) else {}
    notes_raw = phrase.get("notes", [])

    notes = []
    for note_entry in notes_raw:
        if not isinstance(note_entry, dict):
            continue

        note = note_entry.get("note")
        time = note_entry.get("time")
        if isinstance(note, str) and isinstance(time, (int, float)):
            notes.append({
                "note": note,
                "time": float(time),
            })

    if not notes:
        raise HTTPException(status_code=404, detail="Reference notes not found")

    phrase_id = phrase.get("id") if isinstance(phrase.get("id"), int) else phrase_index
    phrase_section = phrase.get("section") if isinstance(phrase.get("section"), str) else None
    reference_tempo = song_data.get("base_tempo")
    if not isinstance(reference_tempo, (int, float)):
        reference_tempo = song_data.get("tempo")
    if not isinstance(reference_tempo, (int, float)):
        reference_tempo = None

    return {
        "song_id": song_id,
        "title": song_data.get("title", song_id),
        "content_type": infer_content_type(song_data, song_id),
        "phrase_index": phrase_index,
        "phrase_id": phrase_id,
        "phrase_section": phrase_section,
        "phrase_count": len(phrases),
        "reference_tempo": int(reference_tempo) if isinstance(reference_tempo, (int, float)) else None,
        "notes": notes,
    }
