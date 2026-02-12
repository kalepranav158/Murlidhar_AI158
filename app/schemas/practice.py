from pydantic import BaseModel
from typing import List


class PlayedNote(BaseModel):
    note: str
    cents: float
    time: float


class Evaluation(BaseModel):
    note_accuracy: float
    avg_pitch_error_cents: float
    avg_timing_error_sec: float
    mistakes: list
    feedback: str


class PracticeResponse(BaseModel):
    song: str
    phrase_index: int
    dtw_cost: float
    evaluation: Evaluation
    played_notes: List[PlayedNote]
