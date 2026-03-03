from fastapi import APIRouter, Query

from app.services.analytics_engine import compute_analytics
from app.services.curriculum_service import evaluate_curriculum_progress
from database.db import get_practice_streak
from app.routes.response_envelope import no_data_response


router = APIRouter(prefix="/student", tags=["Student"])


@router.get("/profile")
def get_student_profile(user_id: str = Query(...)):
    curriculum = evaluate_curriculum_progress(user_id)

    return {
        "current_level": curriculum.get("current_level", "beginner"),
        "unlocked_content": curriculum.get("unlocked_content", []),
        "mastered_content": curriculum.get("mastered_content", []),
        "recommended_content": curriculum.get("recommended_content"),
        "composite_score": (
            (curriculum.get("skill_snapshot") or {}).get("composite_score")
        ),
        "reason": curriculum.get("reason"),
    }


@router.get("/curriculum")
def get_student_curriculum(user_id: str = Query(...)):
    return evaluate_curriculum_progress(user_id)


@router.get("/analytics")
def get_student_analytics(user_id: str = Query(...)):
    analytics = compute_analytics(user_id)

    if analytics is None:
        return no_data_response("Not enough sessions.")

    return analytics


@router.get("/streak")
def get_student_streak(user_id: str = Query(...)):
    return get_practice_streak(user_id)
