from pydantic import BaseModel
from typing import List, Optional


class PlayedNote(BaseModel):
    note: str
    cents: float
    time: float


class EvaluationResult(BaseModel):
    note_accuracy: float
    avg_pitch_error_cents: Optional[float]
    avg_timing_error_sec: Optional[float]
    mistakes: List[dict]
    feedback: str


class PracticeResponse(BaseModel):
    song: str
    phrase_index: int
    dtw_cost: float
    evaluation: EvaluationResult
    played_notes: List[PlayedNote]
