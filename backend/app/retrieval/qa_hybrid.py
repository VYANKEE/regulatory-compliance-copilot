"""
Phase 4 QA pipeline: hybrid retrieval (BM25 + dense, RRF) -> top-10 candidates
-> cross-encoder rerank -> top-5 -> same citation-constrained LLM call as
qa_baseline.py.

Important concept: retrieval aur rerank do alag stages hain jaan-boojhkar.
Hybrid retrieval SAB documents me se fast tareeke se ek badi shortlist
(candidates) nikalta hai. Reranker sirf usi chhoti shortlist ko slow-par-accurate
tareeke se sort karta hai. Agar reranker seedha poore corpus pe chalate, latency
bahut badh jaati (71 chunks abhi thik hai, par jaise corpus badhega — 10,000+
chunks — reranker sabpe chalana impossible ho jayega).
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from hybrid_retriever import build_hybrid_retriever
from qa_baseline import PROMPT, format_context
from reranker import rerank


def retrieve_v2(hybrid_retriever, question: str, candidate_k: int = 10, final_k: int = 5):
    candidates = hybrid_retriever.invoke(question)[:candidate_k]
    return rerank(question, candidates, top_k=final_k)



def _content_to_text(content) -> str:
    """Gemini kabhi kabhi response.content ek plain string ki jagah list of
    parts deta hai (multi-part / AFC response shape). Ise hamesha ek plain
    string me normalize karte hain taaki downstream scoring (metrics.py) safe
    rahe."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", ""))
        return "".join(parts)
    return str(content)

def answer(hybrid_retriever, question: str) -> dict:
    docs = retrieve_v2(hybrid_retriever, question)
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)
    chain = PROMPT | llm
    response = chain.invoke({"context": format_context(docs), "question": question})
    return {
        "question": question,
        "answer": _content_to_text(response.content),
        "retrieved_chunk_ids": [d.metadata["chunk_id"] for d in docs],
    }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    retriever = build_hybrid_retriever(k=10)
    result = answer(retriever, "DLG ka cap kitna hai?")
    print(result["answer"])
    print("\nRetrieved:", result["retrieved_chunk_ids"])
