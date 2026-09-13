"""
Cross-encoder reranker.

Important concept: retrieval (BM25/dense) query aur document ko ALAG-ALAG
embed karta hai, phir compare karta hai — fast hai par kam accurate (query aur
document ek dusre ko "dekhte" nahi embedding banate waqt). Cross-encoder query
+ document ko EK SAATH model me daalta hai, isliye zyada accurate hai — par
slow hai (har candidate ke liye ek forward pass). Isliye hum ise retrieval ke
baad, sirf TOP-N candidates pe use karte hain — sabhi documents pe nahi,
warna latency bahut badh jaayegi.
"""

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

_model = None


def get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _model


def rerank(query: str, docs: list[Document], top_k: int = 5) -> list[Document]:
    """docs (retrieval se aaye candidates) ko query ke against rerank karta hai,
    top_k best return karta hai."""
    if not docs:
        return []
    pairs = [(query, d.page_content) for d in docs]
    scores = get_model().predict(pairs)
    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in ranked[:top_k]]


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from bm25_retriever import build_bm25_retriever

    candidates = build_bm25_retriever(k=10).invoke("DLG cap kitna hai")
    print("Before rerank:")
    for d in candidates[:5]:
        print(" ", d.metadata["chunk_id"])

    reranked = rerank("DLG cap kitna hai", candidates, top_k=3)
    print("\nAfter rerank (top 3):")
    for d in reranked:
        print(" ", d.metadata["chunk_id"], "-", d.page_content[:80])
