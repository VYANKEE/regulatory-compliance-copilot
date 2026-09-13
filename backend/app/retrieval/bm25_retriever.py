"""
BM25 = keyword/lexical search. Dense (Chroma) embeddings dono documents ko
"meaning" ke hisaab se match karte hain — isliye exact term match kabhi miss
ho jaata hai (jaise "Para 23" ya "CIMS portal" jaisa specific term). BM25 in
exact matches ko pakadta hai, meaning wale match miss kar sakta hai. Dono
alag-alag weakness cover karte hain — isi wajah se hybrid banate hain (agla
file: hybrid_retriever.py).
"""

import json
from pathlib import Path

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parents[3]
CHUNKS_PATH = ROOT / "data" / "processed" / "chunks.jsonl"


def load_documents() -> list[Document]:
    docs = []
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            docs.append(
                Document(
                    page_content=c["text"],
                    metadata={
                        "chunk_id": c["chunk_id"],
                        "circular_ref": c["circular_ref"],
                        "status": c["status"],
                        "para_no": c["para_no"] or "",
                    },
                )
            )
    return docs


def build_bm25_retriever(k: int = 5) -> BM25Retriever:
    retriever = BM25Retriever.from_documents(load_documents())
    retriever.k = k
    return retriever


if __name__ == "__main__":
    retriever = build_bm25_retriever(k=3)
    for doc in retriever.invoke("DLG cap 5%"):
        print(f"[{doc.metadata['chunk_id']}] {doc.page_content[:100]}...")
