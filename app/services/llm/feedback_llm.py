from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm.gemini_client import get_llm
from app.schemas.Pydantic_schemas import LivePracticeResponse
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def generate_guru_feedback(result: dict):

    llm = get_llm()

    parser = PydanticOutputParser(pydantic_object=LivePracticeResponse)

    system_prompt =system_prompt = """
You are a senior Hindustani classical flute guru.

You MUST respond ONLY in valid JSON.

The JSON must match exactly this schema:

{{
  "mode": "live_practice",
  "overall_accuracy": float,
  "average_pitch_error_cents": float,
  "average_timing_error_seconds": float,
  "pitch_stability_score": float,
  "rhythm_stability_score": float,
  "technical_assessment": string,
  "root_cause_analysis": string,
  "corrective_guidance": string,
  "structured_practice_plan": string,
  "mistake_breakdown": string,
  "confidence_score": float
}}

Rules:
- Do not add extra keys
- Do not nest objects unless defined
- Do not include explanations outside JSON
- No markdown
- No headings
- Only raw JSON
"""


    human_prompt = f"""
Performance Data:
Accuracy: {result['note_accuracy']}%
Pitch Error: {result['avg_pitch_error_cents']} cents
Timing Error: {result['avg_timing_error_sec']} sec
Mistakes: {result['mistakes']}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt),
    ])

    chain = prompt | llm | parser

    response = chain.invoke({
        "format_instructions": parser.get_format_instructions()
    })

    return response.dict()
