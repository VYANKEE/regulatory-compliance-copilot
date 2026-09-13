"""
Shared text-cleanup utility for the LLM-facing agents (diff/impact/verifier).

The source PDFs carry a diagonal "Withdrawn" watermark whose letters got
extracted character-by-character and spliced into the paragraph text as
stray one-letter lines (found in 42/71 corpus chunks). This isn't cosmetic:
it plausibly caused several confirmed-false "not grounded" drops in
VerifierAgent's strict close-reading check on otherwise-exact matches.

Scope is deliberately conservative -- only removes whole lines that are
exactly one of the letters in "Withdrawn" (case-sensitive), after two
earlier broader versions were caught eating real content in testing (a
generic single-letter-line match, and a trailing-fused-letter strip that
deleted a genuine word-wrapped "a"). The residual noise this leaves
(an occasional fused letter) is a minor perturbation an LLM reads past
easily, unlike a bare interrupting line.

Applied at point-of-use rather than to the files on disk, so it works
immediately without re-chunking or re-embedding the corpus.
"""

import re

# Exact letters of "Withdrawn", case-sensitive -- not a generic [A-Za-z]
# class (see module docstring: that over-broad version ate real content).
_WATERMARK_LINE = re.compile(r"\s*[nwardhtiW]\s*")


def clean_watermark_noise(text: str) -> str:
    lines = text.split("\n")
    cleaned = [ln for ln in lines if not _WATERMARK_LINE.fullmatch(ln)]
    return "\n".join(cleaned)
