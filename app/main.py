from fastapi import FastAPI
from app.routes import practice,songs

app = FastAPI(title="Murlidhar AI - Flute Tutor API")

app.include_router(practice.router)
app.include_router(songs.router)

@app.get("/")
def root():
    return {"message": "Flute Tutor API Running"}
