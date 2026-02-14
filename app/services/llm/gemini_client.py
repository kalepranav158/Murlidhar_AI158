import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------
# Singleton LLM Instance
# ----------------------------------

_llm_instance = None

def get_llm():
    global _llm_instance

    if _llm_instance is None:
        _llm_instance = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            temperature=0.4
        )

    return _llm_instance
