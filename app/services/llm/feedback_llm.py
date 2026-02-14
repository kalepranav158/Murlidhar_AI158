from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm.gemini_client import get_llm


def generate_guru_feedback(result: dict) -> str:
    llm = get_llm()

    system_prompt = """
    You are a senior Hindustani classical flute guru.
    Give structured feedback in:
    1. Technical diagnosis
    2. Flute correction advice
    3. Practice recommendation
    """

    human_prompt = f"""
    Performance Data:
    Accuracy: {result['note_accuracy']}%
    Pitch Error: {result['avg_pitch_error_cents']} cents
    Timing Error: {result['avg_timing_error_sec']} sec
    Mistakes: {result['mistakes']}
    """

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])

    return response.text.strip()
