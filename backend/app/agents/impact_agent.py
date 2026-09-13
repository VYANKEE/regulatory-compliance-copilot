"""
Impact Agent -- outputs structured JSON (not free text) so the Verifier
Agent can check each finding independently and granularly.
"""

import json
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from text_cleanup import clean_watermark_noise

PROMPT = ChatPromptTemplate.from_messages(
    [
        # See diff_agent.py's PROMPT -- without this, the reasoning model
        # dumps chain-of-thought instead of strict JSON, breaking _parse_json_list().
        ("system", "detailed thinking off"),
        (
            "human",
            """Tu ek compliance gap-analysis assistant hai. Neeche ek topic ke RBI
requirement clauses aur ek NBFC ki internal policy ka text diya gaya hai.
Bata ki policy is requirement ko poora karti hai ya nahi.

Rules:
- Sirf diye gaye RBI clauses ke against check kar, apni taraf se RBI rules
  mat maan.
- Agar policy me kuch mention hi nahi hai jo requirement maangta hai, status
  "Not Met" do.
- Agar policy me hai par incomplete/vague hai, status "Partial" do.
- Agar policy poora requirement cover karti hai, status "Met" do.
- Response SIRF ek JSON array do, koi extra text nahi, is exact shape me:
[{{"requirement": "...", "status": "Met|Partial|Not Met", "rbi_citation": "chunk_id", "explanation": "...", "suggested_policy_change": "..."}}]
- "rbi_citation" field me SIRF bare chunk_id likh, jaise RBI/2025-26/36::23 --
  koi square brackets '[' ']' iske around MAT laga, chahe RBI CURRENT
  CLAUSES section me chunks isi tarah bracket me dikhaye gaye hon (wo
  sirf tere padhne ke liye ek visual marker hai, JSON output ka format
  nahi hai).
- Agar "Met" hai to suggested_policy_change me "" (khaali string) de.
- Agar RBI clauses me is topic pe kuch nahi mila, ek single item do jisme
  requirement="(no current requirement found for this topic)" aur status="Met".
- "requirement", "explanation" aur "suggested_policy_change" fields ka text
  HAMESHA clear, professional ENGLISH me likh (ye ek real compliance memo
  ka hissa hai jo regulatory/legal reviewers padhenge) -- Hindi/Hinglish
  words in fields me mat use kar, chahe instructions khud Hinglish me hain.
- Agar tujhe pehle soch-vichaar karna hai to kar sakta hai, koi problem
  nahi. Par uske BAAD, EXACT is line se shuru kar (bilkul yehi text, kuch
  aur nahi): ###FINAL_ANSWER### -- us line ke turant baad SIRF JSON array
  ho, koi reasoning/extra commentary nahi.

TOPIC: {topic}

RBI CURRENT CLAUSES:
{current_context}

NBFC POLICY TEXT:
{policy_text}

JSON (soch sakta hai, par ###FINAL_ANSWER### ke baad sirf JSON array):""",
        ),
    ]
)

FINAL_MARKER = "###FINAL_ANSWER###"


def _extract_final(text: str) -> str:
    """See diff_agent.py's _extract_final -- needed even more here since any
    leaked reasoning preamble makes json.loads() fail outright."""
    if FINAL_MARKER in text:
        return text.rsplit(FINAL_MARKER, 1)[-1].strip()
    return text.strip()


def _content_to_text(content) -> str:
    """Gemini kabhi kabhi response.content ek plain string ki jagah list of
    parts deta hai (multi-part / AFC response shape). Ise hamesha ek plain
    string me normalize karte hain."""
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


def _format(docs) -> str:
    if not docs:
        return "(koi clause nahi mila)"
    # Strips watermark noise (see text_cleanup.py) so this matches the clean
    # text VerifierAgent checks against later.
    return "\n\n".join(f"[{d.metadata['chunk_id']}] {clean_watermark_noise(d.page_content)}" for d in docs)


def _parse_json_list(text: str) -> list[dict]:
    """Gemini kabhi kabhi JSON ko ```json ... ``` fence me wrap kar deta hai —
    ise strip karke parse karte hain. Parse fail ho to raw text ek fallback
    finding ke roop me return karte hain (data loss nahi hona chahiye)."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return [
            {
                "requirement": "(JSON parse failed — raw model output)",
                "status": "Partial",
                "rbi_citation": "",
                "explanation": cleaned[:500],
                "suggested_policy_change": "",
            }
        ]


class ImpactAgent:
    def __init__(self):
        # Same NVIDIA NIM / token / timeout tuning as DiffAgent.__init__ (see
        # there for the full reasoning) -- a truncated response here is
        # invalid JSON, not just messy, so it matters even more.
        self.llm = ChatNVIDIA(
            model="nvidia/nemotron-3-super-120b-a12b", temperature=0, max_completion_tokens=16384, timeout=120
        ).with_retry(
            wait_exponential_jitter=True,
            stop_after_attempt=3,
        )

    def assess(self, topic: str, current_docs, policy_text: str) -> list[dict]:
        chain = PROMPT | self.llm
        response = chain.invoke(
            {"topic": topic, "current_context": _format(current_docs), "policy_text": policy_text}
        )
        text = _extract_final(_content_to_text(response.content))
        findings = _parse_json_list(text)
        for f in findings:
            f["topic"] = topic
        return findings
