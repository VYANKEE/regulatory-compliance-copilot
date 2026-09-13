"""
Golden eval set ko baseline RAG (Phase 3, plain semantic search) ke against
chalata hai. Scoring logic `metrics.py` me hai (v1 aur v2 dono isi se score
hote hain, taaki comparison fair rahe).
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "retrieval"))

from qa_baseline import answer  # noqa: E402
from vectorstore import load_vectorstore  # noqa: E402

from metrics import score_item, summarize  # noqa: E402

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
    for item in items:
        result = answer(store, item["question"], k=5)
        record = score_item(item, result)
        results.append(record)
        status = record.get("retrieval_hit", record.get("abstained_correctly"))
        print(f"[{item['id']}] {item['category']} -> {'OK' if status else 'CHECK'}")

    with open(RESULTS_OUT, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    s = summarize(results)
    print("\n=== BASELINE — Phase 3 (plain semantic search) ===")
    if s["retrieval_total"]:
        print(f"Retrieval hit-rate: {s['retrieval_hit']}/{s['retrieval_total']} = {s['retrieval_hit'] / s['retrieval_total']:.0%}")
    if s["abstain_total"]:
        print(f"Correct abstention: {s['abstain_hit']}/{s['abstain_total']} = {s['abstain_hit'] / s['abstain_total']:.0%}")
    print(f"\nFull results -> {RESULTS_OUT}")


if __name__ == "__main__":
    run()
