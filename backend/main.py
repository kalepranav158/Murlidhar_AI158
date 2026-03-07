from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.api import practice,songs
import os
import json
from backend.api import sessions
from backend.api import analytics
from backend.api import ask
from backend.api import debug
from backend.api import student
from backend.api import auth
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


app = FastAPI(title="VENORA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# always initialize database on startup
@app.on_event("startup")
async def startup_event():
    from backend.models.db import init_db
    from backend.services.learning_engine import initialize_learning_model

    init_db()

    try:
        initialize_learning_model()
    except Exception:
        logging.exception("Learning model initialization failed")






app.include_router(practice.router)
app.include_router(songs.router)
app.include_router(sessions.router)
app.include_router(analytics.router)
app.include_router(ask.router)
app.include_router(student.router)
app.include_router(auth.router)

DEBUG_ENDPOINTS_ENABLED = os.getenv("DEBUG_ENDPOINTS", "false").lower() == "true"
if DEBUG_ENDPOINTS_ENABLED:
    app.include_router(debug.router)




@app.get("/")
def root():
    return {"message": "Running well"}



def load_phrase(song_id: str, phrase_id: int):
    path = os.path.join("data", "songs", "catalog", f"{song_id}.json")

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
