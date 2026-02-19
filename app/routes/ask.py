from fastapi import APIRouter
from pydantic import BaseModel
from app.services.llm.ask_llm import ask_guru
from app.schemas.Pydantic_schemas import ASKResponse

router = APIRouter(prefix="/ask", tags=["Ask Guru"])

class QuestionRequest(BaseModel):
    question: str

@router.post("/", response_model=ASKResponse)
async def ask(request: QuestionRequest, user_id: str):
    answer = ask_guru(user_id, request.question)
    return answer
