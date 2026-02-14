from app.services.llm.rag_store import build_vector_store

vector_store = None

def retrieve_context(query: str, k: int = 3):
    vector_store = get_vector_store()
    docs = vector_store.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in docs])


def get_vector_store():
    global vector_store
    if vector_store is None:
        vector_store = build_vector_store()
    return vector_store