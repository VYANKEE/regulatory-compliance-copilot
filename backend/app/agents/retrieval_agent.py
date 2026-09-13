"""
Retrieval Agent -- does status-aware retrieval, not plain top-k: for a topic
like "DLG cap" it needs both the repealed circular's clause and the current
one's, so the Diff Agent can compare them.

Uses the plain-similarity retriever (not the hybrid+rerank pipeline) since
hybrid measured lower on eval (82% -> 77%) -- a measured decision, not a
default choice.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "retrieval"))

from vectorstore import load_vectorstore  # noqa: E402


class RetrievalAgent:
    def __init__(self):
        self.store = load_vectorstore()

    def get_context(self, topic: str, k: int = 12) -> dict:
        """Fetches relevant chunks for a topic, split by status (current vs
        repealed circulars) -- the Diff Agent needs both."""
        docs = self.store.similarity_search(topic, k=k)
        current = [d for d in docs if d.metadata.get("status") == "current"]
        repealed = [d for d in docs if d.metadata.get("status") == "repealed"]
        return {"topic": topic, "current": current, "repealed": repealed}


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = RetrievalAgent()
    result = agent.get_context("Default Loss Guarantee DLG cap")
    print(f"current: {[d.metadata['chunk_id'] for d in result['current']]}")
    print(f"repealed: {[d.metadata['chunk_id'] for d in result['repealed']]}")
