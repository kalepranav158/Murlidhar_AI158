import os
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.services.llm.rag_loader import load_documents

PERSIST_DIR = "app/vector_db"


def build_vector_store():
    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001"
    )

    # If DB already exists → load it
    if os.path.exists(PERSIST_DIR):
       print("Loading existing vector store...")
       return Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings
        )
    
    print("Building new vector store...")
    # Otherwise build it once
    docs = load_documents()

    vector_store = Chroma.from_documents(
        docs,
        embeddings,
        persist_directory=PERSIST_DIR
    )

    vector_store.persist()
    print("vector store built and persisted.")

    return vector_store
