from fastapi import APIRouter, Query
from backend.models.db import get_sessions
from backend.api.response_envelope import no_data_response

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/")
def list_sessions(user_id: str , limit: int = Query(20, ge=1, le=100)):
    sessions = get_sessions(user_id=user_id, limit=limit)

    if not sessions:
        return no_data_response("No sessions available.", data={"count": 0, "sessions": []})

    return {
        "count": len(sessions),
        "sessions": sessions
    }

