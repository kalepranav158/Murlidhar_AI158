from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import JSONResponse
from app.routes import practice,songs
import os
import json
from app.routes import sessions
from app.routes import analytics

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


app = FastAPI(title="Murlidhar AI - Flute Tutor API")

app.include_router(practice.router)
app.include_router(songs.router)
app.include_router(sessions.router)
app.include_router(analytics.router)





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




@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
