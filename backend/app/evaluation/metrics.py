"""
Golden-set scoring — shared by baseline (Phase 3) aur hybrid (Phase 4) eval
runners, taaki dono EXACT same tarike se score ho (warna comparison hi
meaningless ho jaayega).
"""

import re


def score_item(item: dict, result: dict) -> dict:
    """Ek golden-set item + system ka result -> scored record (retrieval_hit
    ya abstained_correctly field ke saath)."""
    record = {**item, "system_answer": result["answer"], "retrieved": result["retrieved_chunk_ids"]}

    if item["category"] in ("grounded", "diff", "diff_partial_source") and item.get("source_clause"):
        expected_paras = set(re.findall(r"\d+", item["source_clause"]))
        found = any(
            cid.startswith("RBI/2025-26/36::") and cid.split("::")[-1] in expected_paras
            for cid in result["retrieved_chunk_ids"]
        )
        record["retrieval_hit"] = found

    if item["category"] == "unanswerable":
        record["abstained_correctly"] = "pata nahi" in result["answer"].lower()

    return record


def summarize(results: list[dict]) -> dict:
    grounded = [r for r in results if "retrieval_hit" in r]
    unanswerable = [r for r in results if "abstained_correctly" in r]
    hit = sum(r["retrieval_hit"] for r in grounded)
    abstained = sum(r["abstained_correctly"] for r in unanswerable)
    return {
        "retrieval_hit": hit,
        "retrieval_total": len(grounded),
        "abstain_hit": abstained,
        "abstain_total": len(unanswerable),
    }
