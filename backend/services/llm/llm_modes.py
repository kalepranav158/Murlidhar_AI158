def classify_knowledge_subtype(question: str) -> str:

    q = question.lower()

    if any(word in q for word in ["history", "origin", "evolution", "material", "construction", "invented"]):
        return "instrument"

    if any(word in q for word in ["raag", "raga", "aaroha", "avaroha", "thaat", "vadi"]):
        return "raga"

    if any(word in q for word in ["breath", "embouchure", "meend", "gamak", "technique", "fingering"]):
        return "technique"

    return "instrument"  # safe fallback




import re


def classify_intent(question: str) -> str:
    """
    Keyword-based intent classifier.
    Returns: 'coaching', 'knowledge', or 'hybrid'
    """

    q = question.lower().strip()

    # ------------------------------
    # Coaching Keywords (Performance)
    # ------------------------------
    coaching_keywords = [
        "my", "i played", "i am playing", "how did i",
        "mistake", "error", "wrong", "accuracy",
        "pitch", "timing", "laya", "shruti",
        "improve", "practice feedback",
        "why am i", "problem", "issue",
        "breath", "embouchure", "stability"
    ]

    # ------------------------------
    # Knowledge Keywords (Theory)
    # ------------------------------
    knowledge_keywords = [
        "what is", "explain", "define",
        "raga", "raag", "thaat",
        "aaroha", "avaroha",
        "vadi", "samvadi", "pakad",
        "history", "origin",
        "structure", "theory",
        "time of performance",
        "rasa", "tell me about"
    ]

    # ------------------------------
    # Hybrid Indicators
    # ------------------------------
    hybrid_indicators = [
        "why did my",
        "how does this affect my",
        "in my performance",
        "when i play",
        "compare my",
        "relate to my"
    ]

    # ------------------------------
    # Rule 1: Hybrid (highest priority)
    # ------------------------------
    for phrase in hybrid_indicators:
        if phrase in q:
            return "hybrid"

    # ------------------------------
    # Rule 2: Coaching if personal reference + performance word
    # ------------------------------
    if any(k in q for k in coaching_keywords):
        if "my" in q or "i" in q:
            return "coaching"

    # ------------------------------
    # Rule 3: Pure Knowledge
    # ------------------------------
    if any(k in q for k in knowledge_keywords):
        return "knowledge"

    # ------------------------------
    # Fallback Logic
    # ------------------------------
    # If it mentions "raga" but also "improve"
    if "raga" in q and ("improve" in q or "problem" in q):
        return "hybrid"

    # Default safe fallback
    return "knowledge"
