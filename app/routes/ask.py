from fastapi import APIRouter
from app.services.llm.gemini_client import generate_response

router = APIRouter(prefix="/ask", tags=["LLM"])

@router.post("/")
async def ask_question(question: str):

    prompt = f"""
    You are a professional Indian classical flute teacher.

    Answer clearly and accurately:
    {question}
    """

    answer = generate_response(prompt)

    return {
        "question": question,
        "answer": answer
    }
