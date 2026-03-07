from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage
from backend.services.llm.gemini_client import get_llm
from backend.services.llm.memory_store import get_user_memory
from backend.services.llm.context_builder import build_practice_context
from backend.services.llm.analytics_context_builder import build_analytics_context
from backend.services.llm.rag_retriever import retrieve_context
from backend.models.Pydantic_schemas import (
    CoachingModeResponse,
    KnowledgeModeResponse,
    HybridModeResponse,
    LivePracticeResponse,
)
from backend.services.llm.llm_modes import classify_intent, classify_knowledge_subtype
import json



# ----------------------------------
# Main Ask Guru Function
# ----------------------------------
def ask_guru(user_id: str, question: str):

    llm = get_llm()
    intent = classify_intent(question)

    # Build shared components
    practice_context = build_practice_context(user_id)
    analytics_context = build_analytics_context(user_id)
    print("=== ANALYTICS CONTEXT ===")
    print(analytics_context)
    rag_context = retrieve_context(question)

    # ----------------------------------
    # MODE A â€” PERFORMANCE COACHING
    # ----------------------------------
    if intent == "coaching":
        parser = PydanticOutputParser(pydantic_object=CoachingModeResponse)

        format_instructions = parser.get_format_instructions()

        system_prompt = """
You are a senior Hindustani classical flute guru.

You are in PERFORMANCE COACHING mode.

You MUST respond ONLY in valid JSON.

The JSON must match exactly this schema:

{{
  "mode": "coaching",
  "description": "Structured performance analysis and corrective guidance.",
  "technical_assessment": string,
  "root_cause_analysis": string,
  "corrective_guidance": string,
  "structured_practice_plan": string,
  "discipline_note": string,
  "improvement_priority": "pitch_control" | "rhythm_stability" | "breath_control" | "consistency" | "overall_refinement",
  "confidence_score": float
}}

Rules:
- improvement_priority MUST be exactly one of the allowed values
- confidence_score must be between 0 and 1
- Do not add extra keys
- Do not rename fields
- Do not nest objects
- Do not include explanations outside JSON
- No markdown
- No headings
- Only raw JSON
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

    # ----------------------------------
    # MODE B â€” KNOWLEDGE TEACHING
    # ----------------------------------
    elif intent == "knowledge":
        parser = PydanticOutputParser(pydantic_object=KnowledgeModeResponse)
        intent_subtype = classify_knowledge_subtype(question)
        format_instructions = parser.get_format_instructions()
        system_prompt = """
You are a scholarly authority in Hindustani classical music theory.

You are in KNOWLEDGE TEACHING mode.
{{intent_subtype}} is the subtype of the question, which can be "raga", "instrument", or "technique". The response must be structured according to the subtype.
{{format_instructions}}
You MUST respond ONLY in valid JSON.

The JSON must match this schema:

{{
  "mode": "knowledge",
  "subtype": "raga" | "instrument" | "technique",
  "description": "Structured Hindustani classical knowledge response.",
  "topic": string,

  // RAGA FIELDS (required if subtype="raga")
  "thaat": string | null,
  "aaroha": string | null,
  "avaroha": string | null,
  "vadi": string | null,
  "samvadi": string | null,
  "pakad": string | null,
  "time_of_performance": string | null,
  "rasa": string | null,
  "bansuri_playing_guidance": string | null,
  "historical_context": string | null,

  // INSTRUMENT FIELDS (required if subtype="instrument")
  "origin_history": string | null,
  "evolution": string | null,
  "construction_materials": string | null,
  "acoustic_principle": string | null,
  "global_flute_comparison": string | null,
  "role_in_hindustani_music": string | null,
  "modern_development": string | null,

  // TECHNIQUE FIELDS (required if subtype="technique")
  "technique_name": string | null,
  "technical_explanation": string | null,
  "biomechanics": string | null,
  "tonal_impact": string | null,
  "common_errors": string | null,
  "correction_methodology": string | null,
  "advanced_mastery_notes": string | null,

  "confidence_score": float
}}

CRITICAL RULES:
{{
1. If subtype="raga":
   - All raga fields MUST be filled.
   - Instrument and technique fields MUST be null.

2. If subtype="instrument":
   - All instrument fields MUST be filled.
   - Raga and technique fields MUST be null.

3. If subtype="technique":
   - All technique fields MUST be filled.
   - Raga and instrument fields MUST be null.

4. Do not invent raga data if question is about instrument.
5. Do not add extra keys.
6. Do not include explanations outside JSON.
7. No markdown.
8. Only raw JSON.
}}
"""


        human_prompt = """
Explain the following topic in structured classical format:

Topic:
{input}

Use authentic Hindustani classical terminology.
"""


        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human",human_prompt)
        ])

    # ----------------------------------
    # MODE C â€” HYBRID
    # ----------------------------------
    else:  # hybrid
        parser = PydanticOutputParser(pydantic_object=HybridModeResponse)
        format_instructions = parser.get_format_instructions()
        system_prompt = """
You are an advanced Hindustani Bansuri Guru.

You are in HYBRID ANALYSIS mode.

You MUST respond ONLY in valid JSON.

The JSON must match exactly this schema:

{{
  "mode": "hybrid",
  "description": "Integrated theoretical explanation with performance diagnosis.",
  "theoretical_clarification": string,
  "performance_diagnosis": string,
  "root_technical_cause": string,
  "integrated_correction_plan": string,
  "discipline_note": string,
  "key_performance_risk": "pitch_drift" | "rhythm_instability" | "breath_inconsistency" | "technical_execution" | "interpretational_weakness",
  "confidence_score": float
}}

Rules:
- key_performance_risk MUST be exactly one of the allowed values
- confidence_score must be between 0 and 1
- Do not add extra keys
- Do not rename fields
- Do not omit required fields
- Do not include explanations outside JSON
- No markdown
- No headings
- Only raw JSON
"""

        human_prompt = """
Student Performance Data:
{performance_metrics}

Relevant Theory Context:
{rag_context}

Provide integrated diagnosis and correction.
"""


        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", human_prompt)
        ])

    # ----------------------------------
    # Chain Execution
    # ----------------------------------

    chain = prompt | llm |parser

    runnable = RunnableWithMessageHistory(
        chain,
        lambda session_id: get_user_memory(session_id),
        input_messages_key="input",
        history_messages_key="history",
    )

    response = runnable.invoke(
        {
            "input": question,
            "practice_context": practice_context or "",
            "analytics_context": analytics_context or "",
            "rag_context": rag_context or "",
            "format_instructions": parser.get_format_instructions()
        },
        config={"configurable": {"session_id": user_id}},
    )
    
    try:
       return response.dict()

    except Exception as e:
        return {
        "mode": "error",
        "description": "LLM output parsing failed",
        "error_details": str(e),
    }
