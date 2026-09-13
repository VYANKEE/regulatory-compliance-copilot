"""
Hybrid search: BM25 (keyword) + dense (Chroma embeddings) combined via RRF
(Reciprocal Rank Fusion) — hand-written (LangChain ka EnsembleRetriever
moved/changed across versions, isliye khud likha, aur ye samajhne ke liye
bhi better hai).

Important concept: RRF raw similarity SCORES ko average nahi karta (BM25
score aur cosine similarity ke units hi alag hain, unhe directly mix karna
galat hai) — balki har retriever ki RANKING (1st, 2nd, 3rd...) use karta hai:
score = sum(weight / (60 + rank)) har retriever ke across. Jo document dono
retrievers me upar aaya, uska combined score sabse zyada hoga. 60 ek standard
constant hai (paper se) jo top ranks ko zyada dominate karne se rokta hai.
"""

from langchain_core.documents import Document

from bm25_retriever import build_bm25_retriever
from vectorstore import load_vectorstore

RRF_K = 60


def reciprocal_rank_fusion(ranked_lists: list[list[Document]], weights: list[float]) -> list[Document]:
    scores: dict[str, float] = {}
    doc_by_id: dict[str, Document] = {}
    for docs, weight in zip(ranked_lists, weights):
        for rank, doc in enumerate(docs):
            cid = doc.metadata["chunk_id"]
            doc_by_id[cid] = doc
            scores[cid] = scores.get(cid, 0.0) + weight / (RRF_K + rank + 1)
    ranked_ids = sorted(scores, key=scores.get, reverse=True)
    return [doc_by_id[cid] for cid in ranked_ids]


class HybridRetriever:
    def __init__(self, k: int = 10, bm25_weight: float = 0.4, dense_weight: float = 0.6):
        self.bm25 = build_bm25_retriever(k=k)
        self.dense = load_vectorstore().as_retriever(search_kwargs={"k": k})
        self.weights = [bm25_weight, dense_weight]

    def invoke(self, query: str) -> list[Document]:
        bm25_results = self.bm25.invoke(query)
        dense_results = self.dense.invoke(query)
        return reciprocal_rank_fusion([bm25_results, dense_results], self.weights)


def build_hybrid_retriever(k: int = 10, bm25_weight: float = 0.4, dense_weight: float = 0.6) -> HybridRetriever:
    """bm25_weight/dense_weight: dono retrievers ko RRF me kitna vote milta hai.
    Dense ko thoda zyada weight diya hai kyunki hamare sawaal zyadatar
    natural-language hain, keyword-heavy nahi."""
    return HybridRetriever(k=k, bm25_weight=bm25_weight, dense_weight=dense_weight)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    retriever = build_hybrid_retriever(k=5)
    for doc in retriever.invoke("DLG ka cap kitna hai?"):
        print(f"[{doc.metadata['chunk_id']}] {doc.page_content[:100]}...")
