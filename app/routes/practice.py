from fastapi import APIRouter, UploadFile, File
from app.services.practice_service import evaluate_audio
from app.schemas.practice import PracticeResponse

router = APIRouter(prefix="/practice", tags=["Practice"])

from app.schemas.practice import PracticeResponse

@router.post("/{user_id}/{song_id}/{phrase_index}", response_model=PracticeResponse)
async def practice(
    user_id: str,
    song_id: str,
    phrase_index: int,
    file: UploadFile = File(...),
):
    return await evaluate_audio(user_id,file, song_id, phrase_index)
