import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------
# Initialize Gemini Model
# ----------------------------------

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not set in environment variables")

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0.4
)


# ----------------------------------
# Generic Response Generator
# ----------------------------------

def generate_response(prompt: str) -> str:
    """
    Sends prompt to Gemini and returns clean text output.
    """
    response = llm.invoke([HumanMessage(content=prompt)])

    # LangChain returns AIMessage object
    return response.text
