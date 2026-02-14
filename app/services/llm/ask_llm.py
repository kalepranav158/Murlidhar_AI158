from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from app.services.llm.gemini_client import get_llm
from app.services.llm.memory_store import get_user_memory
from app.services.llm.context_builder import build_practice_context
from app.services.llm.rag_retriever import retrieve_context


# ----------------------------------
# Simple Intent Classification (Keyword Based)
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

- coaching → if user is asking about their performance, mistakes, pitch, timing, improvement.
- knowledge → if user is asking about raagas, music theory, structure, techniques.
- hybrid → if user is asking theory + linking to their performance.

Respond with ONLY one word:
coaching
knowledge
or
hybrid

User Query:
{question}
"""

    response = llm.invoke(classification_prompt)
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

    # ----------------------------------
    # MODE A — PERFORMANCE COACHING
    # ----------------------------------
    if intent == "coaching":

        practice_context = build_practice_context(user_id)

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
You are an Experienced Hindustani Bansuri Guru.

You are in PERFORMANCE ANALYSIS mode.

You must:
- Analyze measurable metrics precisely.
- Interpret pitch deviation, timing lag, accuracy percentage.
- Diagnose breath control, embouchure stability, fingering clarity, and laya alignment.
- Provide structured, technical corrections.
- Avoid theoretical raga explanations unless directly required.

Practice Context:
{practice_context}

Respond strictly in this format:

1. Technical Assessment
2. Root Cause Analysis
3. Corrective Technique Guidance
4. Structured Practice Plan
5. Discipline Note

Constraints:
- No emojis
- No exaggerated praise
- No vague motivation
- Be concise and authoritative
"""
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        chain = prompt | llm

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
            },
            config={"configurable": {"session_id": user_id}},
        )

        return response.content
    # ----------------------------------
    # MODE B — KNOWLEDGE / RAGA TEACHING
    # ----------------------------------
    elif intent == "knowledge":

        rag_context = retrieve_context(question)

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
You are a scholarly Hindustani Classical Music Guru.

You are in THEORY TEACHING mode.

Use the retrieved knowledge base content to answer accurately.
Do NOT analyze user performance.
Do NOT mention pitch error or timing metrics.
Focus purely on musical theory and structure.

Knowledge Base Context:
{rag_context}

Structure your explanation as:

1. Thaat
2. Aaroha
3. Avaroha
4. Vadi & Samvadi
5. Important Phrases (Pakad)
6. Time & Rasa
7. Bansuri Playing Notes (if relevant)

Constraints:
- Professional tone
- No emojis
- No motivational language
- Clear structured explanation
"""
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        chain = prompt | llm

        runnable = RunnableWithMessageHistory(
            chain,
            lambda session_id: get_user_memory(session_id),
            input_messages_key="input",
            history_messages_key="history",
        )

        response = runnable.invoke(
            {
                "input": question,
                "rag_context": rag_context or "",
            },
            config={"configurable": {"session_id": user_id}},
        )

        return response.content
    # ----------------------------------
    # MODE C — HYBRID 
    # ----------------------------------
    if intent == "hybrid":

        practice_context = build_practice_context(user_id)
        rag_context = retrieve_context(question)

        prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are an advanced Hindustani Bansuri Guru.

You are in HYBRID ANALYSIS mode.

You must:
- Explain relevant musical theory using Knowledge Context.
- Analyze user performance using Practice Context.
- Connect theory mistakes to performance errors.

Practice Context:
{practice_context}

Knowledge Context:
{rag_context}

Structure response:

1. Theoretical Clarification
2. Performance Diagnosis
3. Root Technical Cause
4. Integrated Correction Plan
5. Discipline Note

Constraints:
- No emojis
- Professional tone
- No generic praise
"""
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

        chain = prompt | llm

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
            "rag_context": rag_context or "",
        },
        config={"configurable": {"session_id": user_id}},
    )

        return response.content
    #-----------------------------------