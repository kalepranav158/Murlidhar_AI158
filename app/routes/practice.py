from fastapi import APIRouter, UploadFile, File
from app.services.practice_service import evaluate_audio
from app.schemas.practice import PracticeResponse

router = APIRouter(prefix="/practice", tags=["Practice"])


@router.post(
    "/{song_id}/{phrase_index}",
    response_model=PracticeResponse
)
async def practice(
    song_id: str,
    phrase_index: int,
    file: UploadFile = File(...)
):
    return await evaluate_audio(file, song_id, phrase_index)
