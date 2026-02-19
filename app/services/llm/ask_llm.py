from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage
from app.services.llm.gemini_client import get_llm
from app.services.llm.memory_store import get_user_memory
from app.services.llm.context_builder import build_practice_context
from app.services.llm.analytics_context_builder import build_analytics_context
from app.services.llm.rag_retriever import retrieve_context
from app.schemas.Pydantic_schemas import (
    CoachingModeResponse,
    KnowledgeModeResponse,
    HybridModeResponse,
    LivePracticeResponse,
)
import json

# ----------------------------------
# Intent Classification
# ----------------------------------
def classify_intent(question: str) -> str:
    """
    Uses LLM to classify user query intent.
    Returns: 'coaching', 'knowledge', or 'hybrid'
    """

    llm = get_llm()

    classification_prompt = f"""
You are an intent classifier for a Hindustani Classical Music AI tutor.

Classify the user query into one of these categories:

- coaching → performance, mistakes, pitch, timing, improvement
- knowledge → raagas, theory, structure, techniques
- hybrid → theory + personal performance connection

Respond with ONLY one word:
coaching
knowledge
or
hybrid

User Query:
{question}
"""

    response = llm.invoke([HumanMessage(content=classification_prompt)])

    content = response.content

    if isinstance(content, list):
    # Extract text safely
        text = "".join(
        item.get("text", "")
        for item in content
        if isinstance(item, dict)
    )
    else:
        text = content

    intent = text.strip().lower()


    if intent not in ["coaching", "knowledge", "hybrid"]:
        return "knowledge"

    return intent


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
    # MODE A — PERFORMANCE COACHING
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
    # MODE B — KNOWLEDGE TEACHING
    # ----------------------------------
    elif intent == "knowledge":
        parser = PydanticOutputParser(pydantic_object=KnowledgeModeResponse)

        format_instructions = parser.get_format_instructions()
        system_prompt = """
You are a scholarly authority in Hindustani classical music theory.

You are in KNOWLEDGE TEACHING mode.

You MUST respond ONLY in valid JSON.

The JSON must match exactly this schema:

{{
  "mode": "knowledge",
  "description": "Scholarly explanation of Hindustani classical theory.",
  "topic": string,
  "thaat": string,
  "aaroha": string,
  "avaroha": string,
  "vadi": string,
  "samvadi": string,
  "pakad": string,
  "time_of_performance": string,
  "rasa": string,
  "bansuri_playing_guidance": string,
  "historical_context": string,
  "confidence_score": float
}}

Rules:
- All fields are mandatory
- confidence_score must be between 0 and 1
- Do not add extra keys
- Do not rename fields
- Do not omit fields
- Do not include performance diagnostics
- Do not include explanations outside JSON
- No markdown
- No headings
- Only raw JSON
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
    # MODE C — HYBRID
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