from app.services.llm.gemini_client import generate_response

def generate_guru_feedback(evaluation: dict) -> str:

    prompt = f"""
    You are an expert Hindustani flute guru.

    Student performance evaluation:
    - Note Accuracy: {evaluation["note_accuracy"]}%
    - Avg Pitch Error: {evaluation["avg_pitch_error_cents"]} cents
    - Avg Timing Error: {evaluation["avg_timing_error_sec"]} sec
    - Mistakes: {evaluation["mistakes"]}

    Provide:
    1. Technical correction advice
    2. Specific flute technique guidance
    3. Practice recommendation
    Keep it concise and practical.
    """

    return generate_response(prompt)
