"""
Baseline RAG: retrieve top-k -> ek seedha LLM call -> citation ke saath jawab.

Important concept: ye Verifier Agent (Phase 5) se pehle wala, sabse simple
version hai — retrieval pe hi poora bharosa hai, koi independent fact-check
nahi. Isliye jaan-boojhkar strict prompt diya hai: "sirf diye gaye context se
jawab do, context me na ho to 'pata nahi' bolo" — taaki hallucination kam ho,
par ye guarantee nahi hai (wo guarantee Verifier Agent dega).
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from retriever import retrieve

PROMPT = ChatPromptTemplate.from_template(
    """Tu ek compliance assistant hai. Neeche diye gaye RBI circular clauses ke
CONTEXT ke aadhar par sawaal ka jawab de.

Rules:
- Sirf CONTEXT me jo likha hai wahi use kar, apni taraf se kuch mat jodna.
- Har fact ke saath uska chunk_id citation zaroor de, jaise [RBI/2025-26/36::10].
- Agar CONTEXT me jawab hai hi nahi, to seedha bol "Pata nahi — is corpus me
  iska jawab available nahi hai." Guess mat kar.

CONTEXT:
{context}

SAWAAL: {question}

JAWAB:"""
)


def format_context(docs) -> str:
    return "\n\n".join(f"[{d.metadata['chunk_id']}] {d.page_content}" for d in docs)


def answer(store, question: str, k: int = 5) -> dict:
    docs = retrieve(store, question, k=k)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    chain = PROMPT | llm
    response = chain.invoke({"context": format_context(docs), "question": question})
    return {
        "question": question,
        "answer": response.content,
        "retrieved_chunk_ids": [d.metadata["chunk_id"] for d in docs],
    }


if __name__ == "__main__":
    from dotenv import load_dotenv

    from vectorstore import load_vectorstore

    load_dotenv()
    store = load_vectorstore()
    result = answer(store, "DLG ka cap kitna hai?")
    print(result["answer"])
    print("\nRetrieved:", result["retrieved_chunk_ids"])
