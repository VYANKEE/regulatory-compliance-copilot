"""
Chunks -> embeddings -> lightweight vector store.

Replaces Chroma: its native Rust bindings crashed silently on this machine
(Windows + Python 3.13), reproducibly, isolated down to collection.add().
Swapped in a tiny numpy-based store instead (embeddings as a .npy matrix,
metadata as JSONL, cosine similarity in plain numpy) -- pure Python/numpy
has no native-binding crash surface. Interface stays Chroma-compatible
(similarity_search, as_retriever) so callers don't need to change.

Embeds in batches for rate-limit safety, retrying on 429s.
"""

import json
import os
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning, module="langchain_nvidia_ai_endpoints")

import numpy as np
from langchain_core.documents import Document
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

ROOT = Path(__file__).resolve().parents[3]
CHUNKS_PATH = ROOT / "data" / "processed" / "chunks.jsonl"
PERSIST_DIR = ROOT / "data" / "vector_store"
VECTORS_PATH = PERSIST_DIR / "vectors.npy"
META_PATH = PERSIST_DIR / "meta.jsonl"
COLLECTION_NAME = "compliance_circulars"  # kept for continuity, not used structurally

BATCH_SIZE = 15
BATCH_PAUSE_SECONDS = 3
RATE_LIMIT_WAIT_SECONDS = 60
MAX_RETRIES_PER_BATCH = 5


def get_embeddings():
    """NVIDIA NIM embedding model. Requires NVIDIA_API_KEY to be set."""
    return NVIDIAEmbeddings(model="nvidia/nemotron-3-embed-1b")


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


class _SimpleRetriever:
    def __init__(self, store: "SimpleVectorStore", k: int):
        self.store = store
        self.k = k

    def invoke(self, query: str):
        return self.store.similarity_search(query, k=self.k)


class SimpleVectorStore:
    """Chroma-compatible drop-in via similarity_search() and as_retriever()."""

    def __init__(self, vectors: np.ndarray, texts: list[str], metadatas: list[dict]):
        self.vectors = vectors  # shape (N, D), already L2-normalized
        self.texts = texts
        self.metadatas = metadatas
        self._embeddings = get_embeddings()

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        qvec = np.array(self._embeddings.embed_query(query), dtype=np.float32)
        qnorm = np.linalg.norm(qvec)
        if qnorm > 0:
            qvec = qvec / qnorm
        sims = self.vectors @ qvec  # cosine similarity (dono normalized hain)
        top_idx = np.argsort(-sims)[:k]
        return [Document(page_content=self.texts[i], metadata=self.metadatas[i]) for i in top_idx]

    def as_retriever(self, search_kwargs: dict | None = None) -> _SimpleRetriever:
        k = (search_kwargs or {}).get("k", 5)
        return _SimpleRetriever(self, k)


def build_vectorstore() -> SimpleVectorStore:
    """Embeds chunks and persists to disk (.npy + .jsonl). Re-run whenever
    chunks.jsonl changes."""
    docs = load_chunks_as_documents()
    embeddings_fn = get_embeddings()

    PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    all_vectors: list[list[float]] = []
    all_texts: list[str] = []
    all_metadatas: list[dict] = []

    total = len(docs)
    for i in range(0, total, BATCH_SIZE):
        batch = docs[i : i + BATCH_SIZE]
        texts = [d.page_content for d in batch]
        metadatas = [d.metadata for d in batch]

        for attempt in range(1, MAX_RETRIES_PER_BATCH + 1):
            try:
                vectors = embeddings_fn.embed_documents(texts)
                all_vectors.extend(vectors)
                all_texts.extend(texts)
                all_metadatas.extend(metadatas)
                print(f"  added {min(i + BATCH_SIZE, total)}/{total} chunks")
                break
            except Exception as e:
                msg = str(e)
                if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                    print(
                        f"  rate limited on batch starting at {i} "
                        f"(attempt {attempt}/{MAX_RETRIES_PER_BATCH}), "
                        f"waiting {RATE_LIMIT_WAIT_SECONDS}s..."
                    )
                    time.sleep(RATE_LIMIT_WAIT_SECONDS)
                else:
                    raise
        else:
            raise RuntimeError(
                f"Batch starting at index {i} failed after {MAX_RETRIES_PER_BATCH} retries"
            )
        time.sleep(BATCH_PAUSE_SECONDS)

    vectors_arr = np.array(all_vectors, dtype=np.float32)
    norms = np.linalg.norm(vectors_arr, axis=1, keepdims=True)
    norms[norms == 0] = 1e-8
    vectors_arr = vectors_arr / norms  # normalize once, so query-time is a plain dot product

    np.save(VECTORS_PATH, vectors_arr)
    with open(META_PATH, "w", encoding="utf-8") as f:
        for text, meta in zip(all_texts, all_metadatas):
            f.write(json.dumps({"text": text, "metadata": meta}, ensure_ascii=False) + "\n")

    print(f"Indexed {total} chunks into vector store at {PERSIST_DIR}")
    return SimpleVectorStore(vectors_arr, all_texts, all_metadatas)


def load_vectorstore() -> SimpleVectorStore:
    """Loads an existing index from disk (no re-embedding)."""
    vectors = np.load(VECTORS_PATH)
    texts, metadatas = [], []
    with open(META_PATH, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            texts.append(rec["text"])
            metadatas.append(rec["metadata"])
    return SimpleVectorStore(vectors, texts, metadatas)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    if not os.getenv("NVIDIA_API_KEY"):
        raise SystemExit("NVIDIA_API_KEY is not set in .env -- set it first.")
    build_vectorstore()
