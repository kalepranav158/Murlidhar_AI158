from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm.gemini_client import get_llm
from app.schemas.Pydantic_schemas import LivePracticeResponse
import json
import logging

logger = logging.getLogger(__name__)


def generate_guru_feedback(result: dict, adaptive_plan: dict):
    """
    Generate guru feedback using LLM.
    Calls LLM directly and parses JSON response without prompt template complications.
    """
    llm = get_llm()

    system_message = SystemMessage(content="""
You are a senior Hindustani classical flute guru.

You MUST respond ONLY in valid JSON. No markdown, no extra text, just raw JSON.

{{
  "mode": "live_practice",
  "overall_accuracy": <float>,
  "average_pitch_error_cents": <float>,
  "average_timing_error_seconds": <float>,
  "pitch_stability_score": <float 0-100>,
  "rhythm_stability_score": <float 0-100>,
  "technical_assessment": "<string>",
  "root_cause_analysis": "<string>",
  "corrective_guidance": "<string>",
  "structured_practice_plan": "<string>",
  "mistake_breakdown": "<string>",
  "tempo_adjustment_recommendation": "<string>",
  "confidence_score": <float 0-1>
}}
""")

    human_message = HumanMessage(content=f"""
Analyze this flute practice session and provide feedback:

Accuracy: {result['note_accuracy']}%
Pitch Error: {result['avg_pitch_error_cents']} cents
Timing Error: {result['avg_timing_error_sec']} seconds
Mistakes: {result['mistakes']}
Real BPM Played: {adaptive_plan.get('real_bpm')}
Tempo Feedback: {adaptive_plan.get('tempo_feedback')}

Respond ONLY with valid JSON, no other text.
""")

    try:
        response = llm.invoke([system_message, human_message])
        
        # Extract JSON from response
        response_text = response.content.strip()
        
        # Strip markdown code block if present (```json ... ```)
        if response_text.startswith("```"):
            # Remove opening ```json or ```
            response_text = response_text.split("\n", 1)[1]
            # Remove closing ```
            response_text = response_text.rsplit("```", 1)[0]
        
        response_text = response_text.strip()
        
        # Try to parse JSON
        feedback_dict = json.loads(response_text)
        return feedback_dict
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        logger.error(f"Response was: {response_text}")
        raise
    except Exception as e:
        logger.error(f"LLM feedback generation failed: {e}")
        raise





# geenrate feedback when llm fails 
def generate_normal_feedback(evaluation):
    feedback = []

    if evaluation["note_accuracy"] < 70:
        feedback.append("Focus on correct note transitions.")
    else:
        feedback.append("Good note accuracy.")

    if evaluation["avg_pitch_error_cents"] > 30:
        feedback.append("Pitch variation is high. Work on embouchure consistency.")
    else:
        feedback.append("Pitch control is stable.")

    if evaluation["avg_timing_error_sec"] > 0.5:
        feedback.append("Rhythmic stability needs improvement. Slow down and hold notes evenly.")
    else:
        feedback.append("Timing is well maintained.")

    return " ".join(feedback)
