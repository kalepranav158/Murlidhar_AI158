import os
from fastapi import APIRouter
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
