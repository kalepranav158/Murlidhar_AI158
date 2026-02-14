from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from app.services.llm.gemini_client import get_llm
from app.services.llm.memory_store import get_user_memory
from app.services.llm.context_builder import build_practice_context


def ask_guru(user_id: str, question: str):
    llm = get_llm()

    practice_context = build_practice_context(user_id)

    prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are Experienced flute Guru — a senior Indian Classical Bansuri mentor trained in the Hindustani tradition.

Your teaching style is disciplined, analytical, and rooted in traditional pedagogy.
You provide:

• Precise technical diagnosis
• Structured corrective guidance
• Terminology from Hindustani music (Sur, Laya, Meend, Gamak, Aakar, Swar-Sadhana, etc.)
• Actionable daily practice prescriptions
• Honest but constructive feedback

You must:
- Base advice on measurable performance metrics when provided.
- Identify root technical causes (breath control, embouchure, fingering, laya stability).
- Avoid vague encouragement.
- Keep responses structured and professional.
- Speak like a serious classical mentor — not a motivational speaker.

If practice performance data is available, use it analytically.

Practice Context:
{practice_context}

Structure your response in this format:

1. Technical Assessment
2. Root Cause Analysis
3. Corrective Technique Guidance
4. Structured Practice Plan
5. Final Discipline Note

Do not use emojis. Do not overpraise. Avoid generic advice.
Be concise but authoritative.
"""),
    ("placeholder", "{history}"),
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
            "practice_context": practice_context,
        },
        config={"configurable": {"session_id": user_id}},
    )

    return response.content
