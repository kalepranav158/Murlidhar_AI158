import os
from fastapi import APIRouter
from music.song_loader import load_song

router = APIRouter(prefix="/songs", tags=["Songs"])

SONGS_FOLDER = "songs"


@router.get("/")
def list_songs():
    songs = []

    for file in os.listdir(SONGS_FOLDER):
        if file.endswith(".json"):
            song_id = file.replace(".json", "")
            song_path = os.path.join(SONGS_FOLDER, file)

            song_data = load_song(song_path)

            songs.append({
                "song_id": song_id,
                "title": song_data.get("title", song_id),
                "tempo": song_data.get("tempo", None),
                "phrases": len(song_data.get("phrases", []))
            })

    return songs
