import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge")


def load_documents():
    documents = []

    if not os.path.exists(KNOWLEDGE_DIR):
        raise ValueError(f"Knowledge directory not found: {KNOWLEDGE_DIR}")

    for filename in os.listdir(KNOWLEDGE_DIR):
        if filename.endswith((".txt", ".text")):
            file_path = os.path.join(KNOWLEDGE_DIR, filename)
            loader = TextLoader(file_path)
            documents.extend(loader.load())

    if not documents:
        raise ValueError("No knowledge documents loaded.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    return splitter.split_documents(documents)
