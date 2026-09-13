"""
Input Guardrails -- plain Python checks that run before any LLM call, so
they're fast (no API call) and can't be talked around by prompt injection,
unlike an "LLM decides if this is safe" guardrail. Cheap checks first,
smarter/expensive ones later if ever needed.
"""

import re

MAX_QUERY_LENGTH = 2000
MIN_QUERY_LENGTH = 3

# Common prompt-injection patterns -- not foolproof, but a cheap first line of defense.
INJECTION_PATTERNS = [
    r"ignore (all |previous |above )?instructions",
    r"you are now",
    r"system prompt",
    r"disregard (the )?(above|previous)",
    r"act as (if )?you",
    r"reveal your (prompt|instructions)",
]

OFF_TOPIC_KEYWORDS_HINT = [
    # Soft signal only, not enforced -- full topic classification would be an
    # LLM-based check, added later if the rule-based false-positive rate is too high.
]


class GuardrailViolation(Exception):
    """Raised when a query fails a guardrail; the API layer turns this into a
    clean 400, never a stack trace."""

    def __init__(self, reason: str, code: str):
        self.reason = reason
        self.code = code
        super().__init__(reason)


def validate_query(query: str) -> str:
    """Validates a query, returning the stripped version. Raises
    GuardrailViolation on failure."""
    if not query or not query.strip():
        raise GuardrailViolation("Query cannot be empty.", code="empty_query")

    query = query.strip()

    if len(query) < MIN_QUERY_LENGTH:
        raise GuardrailViolation("Query is too short.", code="too_short")

    if len(query) > MAX_QUERY_LENGTH:
        raise GuardrailViolation(
            f"Query cannot exceed {MAX_QUERY_LENGTH} characters.", code="too_long"
        )

    lowered = query.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            raise GuardrailViolation(
                "Query contains a suspicious instruction-override pattern.",
                code="possible_injection",
            )

    return query
