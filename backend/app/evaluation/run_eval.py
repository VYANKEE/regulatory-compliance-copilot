"""
Golden eval set ko baseline RAG (Phase 3, plain semantic search) ke against
chalata hai aur do simple metrics measure karta hai:

1. Retrieval hit-rate: grounded/diff sawaalon ke liye, kya sahi source_clause
   top-k retrieved chunks me tha?
2. Abstention rate: unanswerable sawaalon ke liye, kya system ne "pata nahi"
   bola (guess nahi kiya)?

Important concept: ye do metrics alag cheez measure karte hain — pehla
batata hai retrieval kitni achhi hai, dusra batata hai system apni limits
jaanta hai ya nahi. Dono zaroori hain, ek dusre ko replace nahi karte.
Numbers yahan se hi aayenge — kahi aur se copy nahi karna.
"""

import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "retrieval"))

from qa_baseline import answer  # noqa: E402
from vectorstore import load_vectorstore  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
GOLDEN_SET = ROOT / "evals" / "golden_set_v1.jsonl"
RESULTS_OUT = ROOT / "evals" / "results_v1_baseline.jsonl"


def load_golden_set():
    with open(GOLDEN_SET, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def run():
    load_dotenv()
    store = load_vectorstore()
    items = load_golden_set()

    results = []
    hit, grounded_total = 0, 0
    abstained, unanswerable_total = 0, 0

    for item in items:
        result = answer(store, item["question"], k=5)
        record = {**item, "system_answer": result["answer"], "retrieved": result["retrieved_chunk_ids"]}

        if item["category"] in ("grounded", "diff", "diff_partial_source") and item.get("source_clause"):
            grounded_total += 1
            # source_clause jaise "Para 23" ya "Para 1, Para 30" — usme se para
            # numbers nikaal ke check karte hain ki kya wo current (2025)
            # circular ke us para ka chunk retrieve hua.
            expected_paras = set(re.findall(r"\d+", item["source_clause"]))
            found = any(
                cid.startswith("RBI/2025-26/36::") and cid.split("::")[-1] in expected_paras
                for cid in result["retrieved_chunk_ids"]
            )
            record["retrieval_hit"] = found
            hit += int(found)

        if item["category"] == "unanswerable":
            unanswerable_total += 1
            said_pata_nahi = "pata nahi" in result["answer"].lower()
            record["abstained_correctly"] = said_pata_nahi
            abstained += int(said_pata_nahi)

        results.append(record)
        print(f"[{item['id']}] {item['category']} -> {'OK' if record.get('retrieval_hit', record.get('abstained_correctly')) else 'CHECK'}")

    with open(RESULTS_OUT, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\n=== BASELINE — Phase 3 (plain semantic search) ===")
    if grounded_total:
        print(f"Retrieval hit-rate: {hit}/{grounded_total} = {hit / grounded_total:.0%}")
    if unanswerable_total:
        print(f"Correct abstention: {abstained}/{unanswerable_total} = {abstained / unanswerable_total:.0%}")
    print(f"\nFull results -> {RESULTS_OUT}")


if __name__ == "__main__":
    run()
