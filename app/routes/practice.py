from fastapi import APIRouter, UploadFile, File
from app.services.practice_service import evaluate_audio

router = APIRouter(prefix="/practice", tags=["Practice"])

@router.post("/{song_id}/{phrase_index}")
async def practice(
    song_id: str,
    phrase_index: int,
    file: UploadFile = File(...)
):
    result = await evaluate_audio(file, song_id, phrase_index)
    return result
