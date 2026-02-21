from pydantic import BaseModel, Field
from typing import List, Literal, Union, Annotated,Optional


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

    subtype: Literal["raga", "instrument", "technique"]

    description: str = Field(
        default="Structured Hindustani classical knowledge response."
    )

    topic: str

    # Optional fields depending on subtype
    thaat: str | None = None
    aaroha: str | None = None
    avaroha: str | None = None
    vadi: str | None = None
    samvadi: str | None = None
    pakad: str | None = None
    time_of_performance: str | None = None
    rasa: str | None = None

    bansuri_playing_guidance: str | None = None
    historical_context: str | None = None

    # Instrument fields
    origin_history: str | None = None
    evolution: str | None = None
    construction_materials: str | None = None
    acoustic_principle: str | None = None
    global_flute_comparison: str | None = None
    role_in_hindustani_music: str | None = None
    modern_development: str | None = None

    # Technique fields
    technique_name: str | None = None
    technical_explanation: str | None = None
    biomechanics: str | None = None
    tonal_impact: str | None = None
    common_errors: str | None = None
    correction_methodology: str | None = None
    advanced_mastery_notes: str | None = None

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

class ErrorResponse(BaseModel):
    mode: Literal["error"]
    description: str
    error_details: str


# ============================================================
# 6️⃣ Unified Response Type (Discriminated Union)
# ============================================================

ASKResponse = Annotated[
    Union[
        LivePracticeResponse,
        CoachingModeResponse,
        KnowledgeModeResponse,
        HybridModeResponse,
        ErrorResponse
    ],
    Field(discriminator="mode")
]

class AdaptivePlan(BaseModel):
    adaptive_enabled: bool
    recommended_tempo: int  
    focus_area: str
    plateau_intervention: bool
    tempo_feedback: str
    real_bpm: float
    reference_bpm: int
    tempo_deviation: float   