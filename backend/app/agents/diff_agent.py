"""
Diff Agent -- compares only the retrieved old vs new clause text (never the
model's own training knowledge), so the diff stays grounded in real chunks.
"""

import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from text_cleanup import clean_watermark_noise

PROMPT = ChatPromptTemplate.from_messages(
    [
        # Nemotron is a reasoning model -- without this it leaks raw
        # chain-of-thought into the response instead of a clean answer.
        ("system", "detailed thinking off"),
        (
            "human",
            """Tu ek regulatory analyst hai. Neeche ek topic ke baare me PURANE
(repealed) circular ke clauses aur NAYE (current) circular ke clauses diye
gaye hain. Bata ki is topic pe kya badla.

Rules:
- Sirf diye gaye text ke aadhar par bata, apni taraf se RBI rules mat yaad
  kar ke bata.
- Har point ke saath chunk_id citation zaroor de, square brackets me, jaise
  [RBI/2025-26/36::23].
- Agar PURANE clauses me kuch nahi mila is topic pe, saaf bol ki purane
  circulars me is topic pe kuch nahi mila aur ye ek naya requirement hai.
- Agar NAYE clauses me kuch nahi mila, saaf bol ki naye circular me nahi
  mila.
- OUTPUT LANGUAGE/FORMAT (bahut zaroori): final output ek real compliance
  memo ka hissa hai jo regulatory/legal reviewers padhenge -- isliye final
  answer HAMESHA professional, clear ENGLISH me likh (chahe ye instructions
  khud Hinglish me hain). Hindi/Hinglish words final answer me mat use kar.
  Final answer me EXACTLY ye teen Markdown headings use kar, aur kuch nahi:
  ### New or Added Requirements
  ### Changed or Tightened Requirements
  ### Unchanged Requirements
  Har heading ke neeche bullet points (- se shuru), har bullet 1-2 sentences
  ka clear professional English prose, end me chunk_id citation. Agar kisi
  heading ke against kuch nahi hai, "None identified for this topic." likh
  us heading ke neeche.
- In teen headings ke alawa koi aur heading, intro line, ya commentary mat
  likh. Ye instructions repeat mat kar.
- Har heading sirf "### " se shuru ho, aur usi line ke end me koi extra
  '#' character kabhi mat laga (jaise "### Some Heading###" GALAT hai) --
  sirf ek clean heading line likh, kuch aur nahi.
- Agar tujhe pehle soch-vichaar karna hai to kar sakta hai, koi problem
  nahi. Par uske BAAD, EXACT is line se shuru kar (bilkul yehi text, kuch
  aur nahi): ###FINAL_ANSWER### -- us line ke turant baad SIRF upar wala
  professional English format ho, koi reasoning/extra commentary nahi.

TOPIC: {topic}

PURANE (repealed) CLAUSES:
{repealed_context}

NAYE (current) CLAUSES:
{current_context}

DIFF ANALYSIS (soch sakta hai, par ###FINAL_ANSWER### ke baad sirf clean, professional English answer, teen headings ke format me):""",
        ),
    ]
)

FINAL_MARKER = "###FINAL_ANSWER###"


def _extract_final(text: str) -> str:
    """"detailed thinking off" doesn't fully suppress Nemotron's reasoning
    trace, so the prompt asks for an explicit marker and we return only
    what's after it. Falls back to the full text if no marker is found."""
    if FINAL_MARKER in text:
        return text.rsplit(FINAL_MARKER, 1)[-1].strip()
    return text.strip()


def _strip_stray_heading_hashes(text: str) -> str:
    """Model sometimes emits "### Heading###" -- a trailing '###' with no
    space renders as literal text per CommonMark. Strip any trailing '#'
    run from lines that start with '#'; safe since headings here are fixed."""
    cleaned_lines = []
    for line in text.split("\n"):
        if line.lstrip().startswith("#"):
            cleaned_lines.append(re.sub(r"#+\s*$", "", line).rstrip())
        else:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


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
    # Strips the watermark noise spliced into some corpus chunks (see text_cleanup.py).
    return "\n\n".join(f"[{d.metadata['chunk_id']}] {clean_watermark_noise(d.page_content)}" for d in docs)


class DiffAgent:
    def __init__(self):
        # NVIDIA NIM instead of Gemini: reuses the same NVIDIA_API_KEY as the
        # embedding model, and its free tier is credit-pool based rather than
        # Gemini's hard 15 req/min wall. Model picked by actually invoking it
        # (NVIDIA's free catalog churns fast) -- confirmed working 2026-09-11.
        # max_completion_tokens=16384: this reasoning model's chain-of-thought
        # is long enough to get cut off (finish_reason="length") at lower
        # budgets, before ever reaching the ###FINAL_ANSWER### marker.
        # timeout=120 / stop_after_attempt=3: the langchain client's 60s
        # default timeout was too short for some topics' generation time; 120s
        # covers that while keeping a stuck call's worst case bounded (Windows
        # Ctrl+C can't interrupt a blocked network call). A run that still
        # fails here is retried at the job level (api/routes/analysis.py).
        self.llm = ChatNVIDIA(
            model="nvidia/nemotron-3-super-120b-a12b", temperature=0, max_completion_tokens=16384, timeout=120
        ).with_retry(
            wait_exponential_jitter=True,
            stop_after_attempt=3,
        )

    def diff(self, topic: str, current_docs, repealed_docs) -> dict:
        chain = PROMPT | self.llm
        response = chain.invoke(
            {
                "topic": topic,
                "current_context": _format(current_docs),
                "repealed_context": _format(repealed_docs),
            }
        )
        text = _strip_stray_heading_hashes(_extract_final(_content_to_text(response.content)))
        return {
            "topic": topic,
            "diff_text": text,
            "current_chunk_ids": [d.metadata["chunk_id"] for d in current_docs],
            "repealed_chunk_ids": [d.metadata["chunk_id"] for d in repealed_docs],
        }
