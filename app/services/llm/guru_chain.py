from langchain.chains import ConversationalRetrievalChain
from app.services.llm.gemini_client import get_llm
from app.services.llm.rag_retriever import get_retriever
from app.services.llm.memory import get_memory


def get_guru_chain():

    llm = get_llm()
    retriever = get_retriever()
    memory = get_memory()

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        verbose=False
    )

    return chain
