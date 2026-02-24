from pydantic import BaseModel
from typing import List, Optional
from app.schemas.Pydantic_schemas import AdaptivePlan,SongAdaptivePlanResponse



class PlayedNote(BaseModel):
    note: str
    cents: float
    time: float


class EvaluationResult(BaseModel):   # -> this is used in PracticeResponse just below 
    note_accuracy: float
    avg_pitch_error_cents: Optional[float]
    avg_timing_error_sec: Optional[float]
    mistakes: List[dict]
    feedback: Optional[str | dict]
    

class PracticeResponse(BaseModel):
    song: str
    phrase_index: int
    dtw_cost: float
    evaluation: EvaluationResult
    adaptive_plan: AdaptivePlan
    techniques: Optional[dict] = None
    technique_score: Optional[float] = None
    technique_details: Optional[dict] = None
    alankar_level: Optional[dict] = None
    song_adaptive_plan: Optional[SongAdaptivePlanResponse] = None
    full_song_unlocked: bool = False
    played_notes: List[PlayedNote]




    
