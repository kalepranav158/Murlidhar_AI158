import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------
# Singleton LLM Instance
# ----------------------------------

_llm_instance = None


# check for latest model availability
# models Available free



def get_llm():
    global _llm_instance

    if _llm_instance is None:
        _llm_instance = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            top_p=1.0,
        )

    return _llm_instance
