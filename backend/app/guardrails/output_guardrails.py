"""
Output Guardrails -- a deliberately separate layer from the Verifier Agent.
Verifier runs at generation time (LLM grounding-check); these run right
before a response leaves the API -- cheap, deterministic, non-LLM checks
that act as a last safety net if the Verifier itself regresses.

Checks:
1. Every "Not Met"/"Partial" finding has a citation that really exists in
   the corpus (re-verified independently here, not just trusted from upstream).
2. No raw PII pattern (PAN/Aadhaar-shaped) leaks into the report.
3. The report isn't empty or suspiciously short (a sign of upstream failure).
"""

import json
import re
from pathlib import Path

CHUNKS_PATH = Path(__file__).resolve().parents[3] / "data" / "processed" / "chunks.jsonl"

# Conservative PII-shaped patterns (better a false positive than a leak).
# PAN: 5 letters + 4 digits + 1 letter. Aadhaar: 12 digits, loosely grouped.
PII_PATTERNS = {
    "possible_pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    "possible_aadhaar": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
}

MIN_REPORT_LENGTH = 50


class OutputGuardrailViolation(Exception):
    """Raised when a compiled report fails an output guardrail; the caller
    catches this and sends a safe fallback message instead of the raw report."""

    def __init__(self, reason: str, code: str):
        self.reason = reason
        self.code = code
        super().__init__(reason)


def _load_valid_citations() -> set[str]:
    """Loads all valid chunk_ids from the corpus -- same idea as the
    Verifier Agent, but a deliberately independent copy (no shared state)."""
    valid: set[str] = set()
    if not CHUNKS_PATH.exists():
        return valid
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            valid.add(rec["chunk_id"])
    return valid


def _normalize_citation(citation: str) -> str:
    """Same normalization as the Verifier (strips a trailing sub-clause
    suffix like '(i)') so a granularity mismatch doesn't false-positive."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", citation).strip()


def check_citations_grounded(findings: list[dict]) -> list[str]:
    """Checks each finding's rbi_citation exists in the corpus. Returns the
    list of ungrounded citations (empty = all fine); the caller decides what to do."""
    valid_citations = _load_valid_citations()
    if not valid_citations:
        # Corpus failed to load -- can't blind-pass, but shouldn't crash either.
        return ["CORPUS_UNAVAILABLE"]

    problems = []
    for finding in findings:
        citation = finding.get("rbi_citation", "")
        if not citation:
            problems.append(f"missing citation: {finding.get('requirement', '?')}")
            continue
        if citation in valid_citations:
            continue
        if _normalize_citation(citation) in valid_citations:
            continue
        problems.append(f"ungrounded citation '{citation}': {finding.get('requirement', '?')}")
    return problems


def check_no_pii_leak(text: str) -> list[str]:
    """Scans report text for PII-shaped patterns. Returns matches (empty = clean)."""
    hits = []
    for label, pattern in PII_PATTERNS.items():
        if pattern.search(text):
            hits.append(label)
    return hits


def validate_report(report: str, findings: list[dict]) -> str:
    """Final check before sending the report. Returns it unchanged on pass,
    raises OutputGuardrailViolation on fail."""
    if not report or len(report.strip()) < MIN_REPORT_LENGTH:
        raise OutputGuardrailViolation(
            "Generated report is suspiciously short/empty -- likely an upstream failure.",
            code="report_too_short",
        )

    pii_hits = check_no_pii_leak(report)
    if pii_hits:
        raise OutputGuardrailViolation(
            f"Possible PII pattern found in report: {', '.join(pii_hits)}",
            code="possible_pii_leak",
        )

    citation_problems = check_citations_grounded(findings)
    if citation_problems:
        raise OutputGuardrailViolation(
            f"{len(citation_problems)} finding(s) have an ungrounded/missing citation: "
            f"{citation_problems[0]}"
            + (f" (+{len(citation_problems) - 1} more)" if len(citation_problems) > 1 else ""),
            code="ungrounded_citation",
        )

    return report
