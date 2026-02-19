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

        system_prompt = f"""
You are an Experienced Hindustani Bansuri Guru.

You are in PERFORMANCE ANALYSIS mode.

Respond ONLY in valid JSON.

{parser.get_format_instructions()}

Instructions:
- Each field must contain detailed explanation.
- Write technically.
- No markdown.
- No text outside JSON.

Practice Context:
{{practice_context}}

Performance Analytics:
{{analytics_context}}
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


        system_prompt = f"""
You are a scholarly Hindustani Classical Music Guru.

You are in THEORY TEACHING mode.

Respond ONLY in valid JSON.

{parser.get_format_instructions()}

Instructions:
- Provide structured explanation.
- No markdown.
- No emojis.
- No performance analysis.
- No text outside JSON.

Knowledge Base Context:
{{rag_context}}
"""


        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

    # ----------------------------------
    # MODE C — HYBRID
    # ----------------------------------
    else:  # hybrid
        parser = PydanticOutputParser(pydantic_object=HybridModeResponse)

        system_prompt = f"""
You are an advanced Hindustani Bansuri Guru.

You are in HYBRID ANALYSIS mode.

Respond ONLY in valid JSON.

{parser.get_format_instructions()}

Instructions:
- Combine theory and performance.
- Use analytics when relevant.
- No markdown.
- No emojis.
- No text outside JSON.

Practice Context:
{{practice_context}}

Performance Analytics:
{{analytics_context}}

Knowledge Context:
{{rag_context}}
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
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