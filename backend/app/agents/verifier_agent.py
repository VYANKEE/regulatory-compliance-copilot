"""
Verifier Agent -- independent of Impact Agent. Loads the cited chunk's real
text straight from chunks.jsonl and asks a separate LLM call whether the
claim is actually supported by it. Unsupported or uncited claims are
dropped, never reach the report. Generation and verification are kept as
separate layers on purpose -- a model checking its own output is weak.
"""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from text_cleanup import clean_watermark_noise

ROOT = Path(__file__).resolve().parents[3]
CHUNKS_PATH = ROOT / "data" / "processed" / "chunks.jsonl"

# Max concurrent LLM calls when verifying findings in parallel. 5 is a
# conservative default; lower it if 429s show up on a real run.
VERIFY_CONCURRENCY = 5


def _ts() -> str:
    """See graph.py's _ts. This agent's per-finding calls used to be the
    longest silent stretch in a run, so progress prints matter most here."""
    return datetime.now().strftime("%H:%M:%S")

VERIFY_PROMPT = ChatPromptTemplate.from_messages(
    [
        # Highest-risk agent for a leaked reasoning blob: if raw chain-of-
        # thought contains "YES" anywhere, `"YES" in text.upper()` would
        # false-positive. Uses the same ###FINAL_ANSWER### marker as
        # diff_agent.py / impact_agent.py to guard against that.
        ("system", "detailed thinking off"),
        (
            "human",
            """Tu ek strict fact-checker hai. Neeche ek CLAIM aur uska cited SOURCE
TEXT diya gaya hai. Sirf ye bata ki claim source text se directly support
hoti hai ya nahi.

Rules:
- Agar tujhe pehle soch-vichaar karna hai to kar sakta hai, koi problem
  nahi. Par uske BAAD, EXACT is line se shuru kar (bilkul yehi text, kuch
  aur nahi): ###FINAL_ANSWER### -- us line ke turant baad SIRF ek single
  word "YES" ya "NO" ho, koi aur text nahi.
- Agar marker nahi use kar raha (reasoning zaroorat hi nahi hai), to bhi
  poora reply sirf "YES" ya "NO" hona chahiye.

CLAIM: {claim}

SOURCE TEXT: {source_text}

Answer (soch sakta hai, par ###FINAL_ANSWER### ke baad sirf YES ya NO):""",
        ),
    ]
)

FINAL_MARKER = "###FINAL_ANSWER###"


def _extract_final(text: str) -> str:
    """See diff_agent.py's _extract_final. Critical here: without this, a
    leaked reasoning paragraph could contain "YES" while concluding "NO"
    (or vice versa), giving a silently wrong verdict instead of a broken one."""
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


def _normalize_citation(citation: str, corpus: dict[str, str]) -> str | None:
    """Normalizes citations against corpus keys: strips a trailing sub-clause
    suffix like '(i)' (chunk_ids are paragraph-level), and strips surrounding
    '[...]' brackets the model sometimes copies from the prompt's chunk
    display. A real run once dropped 34/37 valid findings from this bracket
    mismatch alone. Only checks the citation exists -- grounding is checked
    separately below."""
    if citation in corpus:
        return citation

    def _strip_paren(s: str) -> str:
        return re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()

    def _strip_brackets(s: str) -> str:
        s = s.strip()
        if s.startswith("[") and s.endswith("]"):
            return s[1:-1].strip()
        return s

    candidates = [
        _strip_paren(citation),
        _strip_brackets(citation),
        _strip_paren(_strip_brackets(citation)),
        _strip_brackets(_strip_paren(citation)),
    ]
    for base in candidates:
        if base and base in corpus:
            return base
    return None


def _load_corpus_map() -> dict[str, str]:
    m = {}
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            # Cleans the watermark noise spliced into some chunks (see text_cleanup.py).
            m[c["chunk_id"]] = clean_watermark_noise(c["text"])
    return m


class VerifierAgent:
    def __init__(self):
        # This agent makes the most calls (one per finding), so it hit
        # Gemini's free-tier quota first -- same NVIDIA NIM / token /
        # timeout tuning as DiffAgent.__init__ (see there for the full reasoning).
        self.llm = ChatNVIDIA(
            model="nvidia/nemotron-3-super-120b-a12b", temperature=0, max_completion_tokens=16384, timeout=120
        ).with_retry(
            wait_exponential_jitter=True,
            stop_after_attempt=3,
        )
        self.corpus = _load_corpus_map()

    def verify(self, findings: list[dict]) -> list[dict]:
        """Checks each finding; returns only the verified ones (unverified
        are dropped, never silently kept). Instant cases (no citation, or
        citation not in corpus) are resolved without an LLM call; the rest
        run concurrently (VERIFY_CONCURRENCY workers) since each finding's
        grounding check is independent. Result order is restored at the end."""
        chain = VERIFY_PROMPT | self.llm
        total = len(findings)
        results: list[tuple[int, dict | None]] = []  # (original index, kept-finding-or-None)
        to_check: list[tuple[int, dict, str]] = []  # (original index, finding, resolved_chunk_id)

        for i, f in enumerate(findings, 1):
            citation = f.get("rbi_citation", "")
            preview = f.get("requirement", "")[:60]

            # "Met, no requirement found" case needs no citation -- passed through as-is.
            if not citation:
                if "no current requirement found" in f.get("requirement", "").lower():
                    f["verified"] = True
                    f["verification_note"] = "no citation needed (no-requirement case)"
                    results.append((i, f))
                    print(f"[{_ts()}]   [{i}/{total}] {preview}... -> ok (no citation needed)")
                else:
                    f["verified"] = False
                    f["verification_note"] = "dropped: no citation given"
                    results.append((i, None))
                    print(f"[{_ts()}]   [{i}/{total}] {preview}... -> dropped (no citation)")
                continue

            resolved_id = _normalize_citation(citation, self.corpus)
            if resolved_id is None:
                f["verified"] = False
                f["verification_note"] = f"dropped: chunk_id '{citation}' not found in corpus"
                results.append((i, None))
                print(f"[{_ts()}]   [{i}/{total}] {preview}... -> dropped (citation '{citation}' not in corpus)")
                continue
            f["rbi_citation"] = resolved_id  # keep the normalized id for a consistent report
            to_check.append((i, f, resolved_id))

        def _check_one(item: tuple[int, dict, str]) -> tuple[int, dict | None]:
            i, f, resolved_id = item
            source_text = self.corpus[resolved_id]
            preview = f.get("requirement", "")[:60]
            print(f"[{_ts()}]   [{i}/{total}] {preview}... checking against {resolved_id}...")
            t0 = time.monotonic()
            # Only `requirement` is checked (not `requirement + explanation`):
            # `explanation` compares against the NBFC policy text, which this
            # agent never sees, so it's structurally unanswerable from
            # source_text alone -- a real run once dropped 23/32 valid
            # findings from including it.
            claim = f.get("requirement", "")
            response = chain.invoke({"claim": claim, "source_text": source_text})
            text = _extract_final(_content_to_text(response.content))
            is_grounded = "YES" in text.upper()
            elapsed = time.monotonic() - t0

            f["verified"] = is_grounded
            f["verification_note"] = "grounded in cited source" if is_grounded else "dropped: not grounded in cited source"
            print(f"[{_ts()}]   [{i}/{total}] -> {'grounded' if is_grounded else 'dropped (not grounded)'} ({elapsed:.0f}s)")
            return i, (f if is_grounded else None)

        if to_check:
            print(f"[{_ts()}]   running {len(to_check)} grounding check(s), up to {VERIFY_CONCURRENCY} at a time...")
            with ThreadPoolExecutor(max_workers=VERIFY_CONCURRENCY) as ex:
                results.extend(ex.map(_check_one, to_check))

        results.sort(key=lambda r: r[0])
        return [f for _, f in results if f is not None]
