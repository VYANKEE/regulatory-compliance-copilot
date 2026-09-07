"""
Chunks -> embeddings -> Chroma vector store.

Important concept: Chroma yahan EMBEDDED mode me chal raha hai — koi alag
server/process nahi (Qdrant hota to alag service hota). Ye humare scale
(71 chunks) ke liye sahi trade-off hai: ek disk folder (`data/chroma_db/`)
me sab kuch persist ho jaata hai, extra infra nahi. Agar corpus lakhon
documents tak badhta, tab standalone vector DB (Qdrant/Milvus) ki zaroorat
padti — ye humara agla "extraction trigger" hai (ADR-001 me note kiya hai).
"""

import json
import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

ROOT = Path(__file__).resolve().parents[3]
CHUNKS_PATH = ROOT / "data" / "processed" / "chunks.jsonl"
PERSIST_DIR = str(ROOT / "data" / "chroma_db")
COLLECTION_NAME = "compliance_circulars"


def get_embeddings():
    """Gemini ka embedding model. GOOGLE_API_KEY env var me hona zaroori hai."""
    return GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")


def load_chunks_as_documents() -> list[Document]:
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
                        "title": c["title"],
                        "date": c["date"],
                        "status": c["status"],
                        "para_no": c["para_no"] or "",
                        "chapter": c["chapter"] or "",
                    },
                )
            )
    return docs


def build_vectorstore() -> Chroma:
    """Chunks ko embed karke Chroma me disk pe persist karta hai. Ek baar chalana
    hai jab bhi chunks.jsonl badle (naya circular add hua)."""
    docs = load_chunks_as_documents()
    store = Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR,
    )
    print(f"Indexed {len(docs)} chunks into Chroma at {PERSIST_DIR}")
    return store


def load_vectorstore() -> Chroma:
    """Pehle se bani hui index ko disk se load karta hai (dobara embed nahi karta)."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=PERSIST_DIR,
    )


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        raise SystemExit("GOOGLE_API_KEY .env me set nahi hai — pehle wo daal.")
    build_vectorstore()
