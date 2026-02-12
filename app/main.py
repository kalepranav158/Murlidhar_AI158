from fastapi import FastAPI
from app.routes import practice,songs
from fastapi import HTTPException
import os
import json


app = FastAPI(title="Murlidhar AI - Flute Tutor API")

app.include_router(practice.router)
app.include_router(songs.router)

@app.get("/")
def root():
    return {"message": "Flute Tutor API Running"}



def load_phrase(song_id: str, phrase_id: int):
    path = os.path.join("songs", f"{song_id}.json")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Song not found")

    with open(path, "r") as f:
        song = json.load(f)

    for phrase in song["phrases"]:
        if phrase["phrase_id"] == phrase_id:
            return phrase["notes"]

    raise HTTPException(status_code=404, detail="Phrase not found")