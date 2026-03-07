from langchain_core.messages import HumanMessage, SystemMessage
import json
import logging

logger = logging.getLogger(__name__)


def _normalize_llm_feedback(feedback: dict) -> dict:
    """Convert 0-100 scores from guru feedback into 0-1 indices.

    The LLM returns pitch/rhythm stability on a 0-100 scale which
    is inconsistent with the rest of the analytics pipeline.  Normalization
    happens near the service layer now, so make the helper available here.
    """
    for k in ["pitch_stability_score", "rhythm_stability_score"]:
        if k in feedback and isinstance(feedback[k], (int, float)):
            try:
                feedback[k] = round(feedback[k] / 100.0, 3)
            except Exception:
                pass
    return feedback


def generate_guru_feedback(result: dict, adaptive_plan: dict):
    """
    Generate guru feedback using LLM.
    Calls LLM directly and parses JSON response without prompt template complications.
    """
    # Keep the optional LLM dependency lazy so pure helper tests can run
    # without requiring provider-specific packages.
    from backend.services.llm.gemini_client import get_llm

    llm = get_llm()

    system_message = SystemMessage(content="""
You are a senior Hindustani classical flute guru.

You MUST respond ONLY in valid JSON. No markdown, no extra text, just raw JSON.

{{
  "mode": "live_practice",
  "overall_accuracy": <float>,
  "average_pitch_error_cents": <float>,
  "average_timing_error_seconds": <float>,
  "pitch_stability_score": <float 0-100>,  # will be normalized to 0-1 by service
  "rhythm_stability_score": <float 0-100>,  # will be normalized to 0-1 by service
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

