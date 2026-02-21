from fastapi import APIRouter, UploadFile, File
from app.services.practice_service import evaluate_audio
from app.schemas.practice import PracticeResponse
from app.services.adaptive_engine import generate_adaptive_plan

router = APIRouter(prefix="/practice", tags=["Practice"])

@router.post("/{user_id}/{song_id}/{phrase_index}", response_model=PracticeResponse)
async def practice(
    user_id: str,
    song_id: str,
    phrase_index: int,
    
    file: UploadFile = File(...),
):
        return await evaluate_audio(user_id,file, song_id, phrase_index)










def compute_adaptive_tempo(base_bpm, composite_score, rhythm_index):
    
    if composite_score > 0.85:
        return base_bpm + 10
    elif rhythm_index < 0.6:
        return base_bpm - 10
    else:
        return base_bpm    