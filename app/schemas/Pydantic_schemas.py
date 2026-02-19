from pydantic import BaseModel, Field
from typing import List, Literal, Union


# ============================================================
# 1️⃣ Shared Sub-Models
# ============================================================
# not in use for now
class MistakeDetail(BaseModel):
    note: str
    issue_type: Literal["pitch", "timing", "missed_note"]
    deviation_value: float
    recommendation: str


# ============================================================
# 2️⃣ Live Practice (Audio Evaluation Mode)
# ============================================================

class LivePracticeResponse(BaseModel):
    mode: Literal["live_practice"]
    description: str = Field(
        default="Detailed technical evaluation of recorded practice session."
    )

    overall_accuracy: float = Field(..., ge=0, le=100)
    average_pitch_error_cents: float
    average_timing_error_seconds: float

    pitch_stability_score: float = Field(..., ge=0, le=100)
    rhythm_stability_score: float = Field(..., ge=0, le=100)

    technical_assessment: str
    root_cause_analysis: str
    corrective_guidance: str
    structured_practice_plan: str

    mistake_breakdown:str

    confidence_score: float = Field(..., ge=0, le=1)


# ============================================================
# 3️⃣ Coaching Mode (Performance Improvement)
# ============================================================

class CoachingModeResponse(BaseModel):
    mode: Literal["coaching"]
    description: str = Field(
        default="Structured performance analysis and corrective guidance."
    )

    technical_assessment: str
    root_cause_analysis: str
    corrective_guidance: str
    structured_practice_plan: str
    discipline_note: str

    improvement_priority: Literal[
        "pitch_control",
        "rhythm_stability",
        "breath_control",
        "consistency",
        "overall_refinement"
    ]

    confidence_score: float = Field(..., ge=0, le=1)


# ============================================================
# 4️⃣ Knowledge Mode (Raga / Theory Teaching)
# ============================================================

class KnowledgeModeResponse(BaseModel):
    mode: Literal["knowledge"]
    description: str = Field(
        default="Scholarly explanation of Hindustani classical theory."
    )

    topic: str
    thaat: str
    aaroha: str
    avaroha: str
    vadi: str
    samvadi: str
    pakad: str
    time_of_performance: str
    rasa: str

    bansuri_playing_guidance: str
    historical_context: str

    confidence_score: float = Field(..., ge=0, le=1)


# ============================================================
# 5️⃣ Hybrid Mode (Theory + Performance Integration)
# ============================================================

class HybridModeResponse(BaseModel):
    mode: Literal["hybrid"]
    description: str = Field(
        default="Integrated theoretical explanation with performance diagnosis."
    )

    theoretical_clarification: str
    performance_diagnosis: str
    root_technical_cause: str
    integrated_correction_plan: str
    discipline_note: str

    key_performance_risk: Literal[
        "pitch_drift",
        "rhythm_instability",
        "breath_inconsistency",
        "technical_execution",
        "interpretational_weakness"
    ]

    confidence_score: float = Field(..., ge=0, le=1)


# ============================================================
# 6️⃣ Unified Response Type (Discriminated Union)
# ============================================================

LLMResponse = Union[
    LivePracticeResponse,
    CoachingModeResponse,
    KnowledgeModeResponse,
    HybridModeResponse,
]
