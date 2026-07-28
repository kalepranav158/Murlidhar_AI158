from fastapi import APIRouter, UploadFile, File
from backend.services.practice_service import evaluate_alankar, evaluate_melody, evaluate_song, evaluate_song_full
from backend.models.practice import PracticeResponse


router = APIRouter(prefix="/practice", tags=["Practice"])


#########################################
# ALANKAR PRACTICE ENDPOINT
#########################################
@router.post("/alankar/{user_id}/{alankar_id}/{phrase_index}", response_model=PracticeResponse)
async def practice_alankar(
    user_id: str,
    alankar_id: str,
    phrase_index: int,
    tempo: int = 60,
    file: UploadFile = File(...),
    debug: bool = False,
):
    """
    Alankar practice endpoint.
    Handles pitch detection, DTW alignment, level computation, and adaptive recommendations.
    """
    return await evaluate_alankar(
        user_id=user_id,
        upload_file=file,
        alankar_id=alankar_id,
        phrase_index=phrase_index,
        tempo=tempo,
        debug=debug,
    )


#########################################
# SONG PRACTICE ENDPOINT
#########################################
@router.post("/song/{user_id}/{song_id}/{phrase_index}", response_model=PracticeResponse)
async def practice_song(
    user_id: str,
    song_id: str,
    phrase_index: int,
    tempo: int = 60,
    file: UploadFile = File(...),
    debug: bool = False,
):

    """
    Song practice endpoint.
    Handles pitch detection, DTW alignment, phrase mastery tracking, and song unlock logic.
    """
    return await evaluate_song(
        user_id=user_id,
        upload_file=file,
        song_id=song_id,
        phrase_index=phrase_index,
        tempo=tempo,
        debug=debug,
    )


#########################################
# MELODY PRACTICE ENDPOINT
#########################################
@router.post("/melody/{user_id}/{melody_id}/{phrase_index}", response_model=PracticeResponse)
async def practice_melody(
    user_id: str,
    melody_id: str,
    phrase_index: int,
    tempo: int = 60,
    file: UploadFile = File(...),
    debug: bool = False,
):
    """
    Melody practice endpoint.
    Handles phrase-level melody evaluation with melody-domain progression tracking.
    """
    return await evaluate_melody(
        user_id=user_id,
        upload_file=file,
        melody_id=melody_id,
        phrase_index=phrase_index,
        tempo=tempo,
        debug=debug,
        
    )

    
@router.post("/song/full/{user_id}/{song_id}")
@router.post("/practice/song/full/{user_id}/{song_id}")
async def practice_song_full(user_id: str, song_id: str, file: UploadFile, debug: bool = False):
    return await evaluate_song_full(user_id, file, song_id, tempo=60, debug=debug)



def compute_adaptive_tempo(base_bpm, composite_score, rhythm_index):
    if composite_score > 0.85:
        return base_bpm + 10
    elif rhythm_index < 0.6:
        return base_bpm - 10
    else:
        return base_bpm    
    




