"""
Follow-Up Agent -- answers questions on a completed analysis. Grounded via
the same RetrievalAgent as the main pipeline (not the model's own memory),
and declines questions unrelated to RBI/digital-lending compliance.

Does not persist conversation history to the DB (would need a new table +
migration); the frontend keeps it in page state for now.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from retrieval_agent import RetrievalAgent  # noqa: E402
from text_cleanup import clean_watermark_noise  # noqa: E402

PROMPT = ChatPromptTemplate.from_messages(
    [
        # See diff_agent.py -- suppresses reasoning-model chain-of-thought leakage.
        ("system", "detailed thinking off"),
        (
            "human",
            """Tu Niriksh hai -- ek RBI digital-lending compliance copilot ka
follow-up assistant. Neeche ek compliance analysis ka context diya gaya hai:
jis circular pe analysis hua, uske verified findings, aur is sawaal ke liye
retrieval se mile relevant RBI clauses.

Rules:
- Apna jawab SIRF diye gaye RBI clauses aur findings ke against de -- apni
  taraf se RBI rules invent mat kar.
- Agar sawaal is analysis ke kisi specific finding ke baare me hai, us
  finding ka reference use kar.
- Agar sawaal broader RBI/digital-lending-compliance topic pe hai (is
  analysis ke findings se bahar bhi), retrieved clauses ke against answer de.
- Agar sawaal RBI/banking-compliance se bilkul unrelated hai (jaise weather,
  general coding help, kisi aur unrelated cheez ki advice), politely decline
  kar aur user ko is analysis ya RBI compliance se related sawaal poochne ke
  liye keh -- generic assistant ki tarah answer mat de.
- Jawab clear, professional ENGLISH me de (ek real compliance officer
  padhega), 2-4 chhote paragraphs se zyada lamba mat rakh.
- Agar tujhe pehle soch-vichaar karna hai to kar sakta hai. Uske BAAD, EXACT
  is line se shuru kar: ###FINAL_ANSWER### -- us line ke turant baad SIRF
  final answer ho, koi reasoning/extra commentary nahi.

CIRCULAR: {circular_ref}

VERIFIED FINDINGS FROM THIS ANALYSIS:
{findings_context}

RELEVANT RBI CLAUSES (retrieved for this specific question):
{retrieved_context}

QUESTION: {question}

ANSWER (soch sakta hai, par ###FINAL_ANSWER### ke baad sirf final answer):""",
        ),
    ]
)

FINAL_MARKER = "###FINAL_ANSWER###"


def _extract_final(text: str) -> str:
    if FINAL_MARKER in text:
        return text.rsplit(FINAL_MARKER, 1)[-1].strip()
    return text.strip()


def _content_to_text(content) -> str:
    """Same response normalization as impact_agent.py's _content_to_text."""
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


def _format_findings(findings: list[dict]) -> str:
    if not findings:
        return "(no findings recorded for this analysis)"
    lines = []
    for f in findings:
        lines.append(
            f"- [{f.get('status', '?')}] {f.get('requirement', '')} "
            f"(cites {f.get('rbi_citation', '?')}): {f.get('explanation', '')}"
        )
    return "\n".join(lines)


def _format_clauses(docs) -> str:
    if not docs:
        return "(no directly relevant clauses retrieved for this question)"
    # Same watermark cleanup as the other agents (see text_cleanup.py).
    return "\n\n".join(f"[{d.metadata['chunk_id']}] {clean_watermark_noise(d.page_content)}" for d in docs)


class FollowUpAgent:
    def __init__(self):
        self.retrieval = RetrievalAgent()
        # Same model as DiffAgent/ImpactAgent; smaller token/timeout budget
        # since a follow-up answer is much shorter than a full report.
        self.llm = ChatNVIDIA(
            model="nvidia/nemotron-3-super-120b-a12b", temperature=0, max_completion_tokens=2048, timeout=90
        ).with_retry(wait_exponential_jitter=True, stop_after_attempt=3)

    def ask(self, question: str, circular_ref: str, findings: list[dict]) -> dict:
        ctx = self.retrieval.get_context(question, k=6)
        docs = ctx["current"] + ctx["repealed"]

        chain = PROMPT | self.llm
        response = chain.invoke(
            {
                "circular_ref": circular_ref,
                "findings_context": _format_findings(findings),
                "retrieved_context": _format_clauses(docs),
                "question": question,
            }
        )
        answer = _extract_final(_content_to_text(response.content))
        citations = sorted({d.metadata["chunk_id"] for d in docs})
        return {"answer": answer, "citations": citations}


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = FollowUpAgent()
    result = agent.ask(
        "What does the cooling-off period actually require?",
        "RBI/2025-26/36",
        findings=[],
    )
    print(result["answer"])
    print("Citations:", result["citations"])
