"""
Golden eval set ko Phase 4 pipeline (hybrid BM25+dense retrieval + cross-encoder
rerank) ke against chalata hai, aur agar Phase 3 ka baseline result pehle se
maujood hai (`results_v1_baseline.jsonl`), to before/after table bhi dikhata
hai — non-negotiable rule #2: "har naye component ke baad eval dobara, before/
after note karna."
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "retrieval"))

from hybrid_retriever import build_hybrid_retriever  # noqa: E402
from qa_hybrid import answer  # noqa: E402

from metrics import score_item, summarize  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
GOLDEN_SET = ROOT / "evals" / "golden_set_v1.jsonl"
RESULTS_OUT = ROOT / "evals" / "results_v2_hybrid.jsonl"
BASELINE_RESULTS = ROOT / "evals" / "results_v1_baseline.jsonl"


def load_golden_set():
    with open(GOLDEN_SET, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_baseline_summary():
    if not BASELINE_RESULTS.exists():
        return None
    with open(BASELINE_RESULTS, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return summarize(rows)


def run():
    load_dotenv()
    retriever = build_hybrid_retriever(k=10)
    items = load_golden_set()

    results = []
    for item in items:
        result = answer(retriever, item["question"])
        record = score_item(item, result)
        results.append(record)
        status = record.get("retrieval_hit", record.get("abstained_correctly"))
        print(f"[{item['id']}] {item['category']} -> {'OK' if status else 'CHECK'}")

    with open(RESULTS_OUT, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    s = summarize(results)
    baseline = load_baseline_summary()

    print("\n=== PHASE 4 — hybrid (BM25 + dense) + reranker ===")
    if s["retrieval_total"]:
        print(f"Retrieval hit-rate: {s['retrieval_hit']}/{s['retrieval_total']} = {s['retrieval_hit'] / s['retrieval_total']:.0%}")
    if s["abstain_total"]:
        print(f"Correct abstention: {s['abstain_hit']}/{s['abstain_total']} = {s['abstain_hit'] / s['abstain_total']:.0%}")

    if baseline:
        print("\n=== BEFORE / AFTER ===")
        if baseline["retrieval_total"] and s["retrieval_total"]:
            before = baseline["retrieval_hit"] / baseline["retrieval_total"]
            after = s["retrieval_hit"] / s["retrieval_total"]
            print(f"Retrieval hit-rate: {before:.0%} -> {after:.0%}")
        if baseline["abstain_total"] and s["abstain_total"]:
            before = baseline["abstain_hit"] / baseline["abstain_total"]
            after = s["abstain_hit"] / s["abstain_total"]
            print(f"Correct abstention: {before:.0%} -> {after:.0%}")
    else:
        print(f"\n(Baseline {BASELINE_RESULTS.name} nahi mila — pehle run_eval.py chala to before/after table bhi dikhega)")

    print(f"\nFull results -> {RESULTS_OUT}")


if __name__ == "__main__":
    run()
