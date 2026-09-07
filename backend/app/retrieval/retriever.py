"""
Top-k similarity search wrapper.

Important concept: ye abhi PURE semantic (dense embedding) search hai — koi
keyword/BM25 matching nahi. Isliye baseline score kharab aayega agar sawaal
me exact number/term match zaroori ho (jaise "Para 23"). Phase 4 me hybrid
search (BM25 + dense) isi weakness ko fix karega — abhi baseline note karna
hai, fix nahi.
"""

from langchain_chroma import Chroma
from langchain_core.documents import Document


def retrieve(store: Chroma, query: str, k: int = 5) -> list[Document]:
    """Query se sabse relevant top-k chunks nikaalta hai."""
    return store.similarity_search(query, k=k)


if __name__ == "__main__":
    from dotenv import load_dotenv

    from vectorstore import load_vectorstore

    load_dotenv()
    store = load_vectorstore()
    results = retrieve(store, "DLG ka cap kitna hai?", k=3)
    for doc in results:
        print(f"[{doc.metadata['chunk_id']}] {doc.page_content[:150]}...\n")
