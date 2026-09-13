"""
Supervisor Agent -- a deterministic planner: runs Retrieval -> Diff ->
Impact -> Verifier for a fixed list of topics, then hands everything to the
Report Agent. Kept simple on purpose; dynamic routing and checkpointing
live in the LangGraph version (graph.py) instead.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "documents"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "retrieval"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from parser import extract_text  # noqa: E402

from diff_agent import DiffAgent
from impact_agent import ImpactAgent
from report_agent import compile_report
from retrieval_agent import RetrievalAgent
from verifier_agent import VerifierAgent

TOPICS = [
    "Default Loss Guarantee (DLG) cap and structure",
    "Key Fact Statement (KFS) disclosure requirements",
    "Cooling-off / look-up period for digital loans",
    "Reporting to Central Information Management System (CIMS)",
    "Grievance redressal and Lending Service Provider (LSP) responsibilities",
    "Data collection, storage and consent requirements",
]


def run_full_analysis(circular_ref: str, policy_pdf_path: str) -> str:
    print(f"Loading policy from {policy_pdf_path}...")
    policy_text = extract_text(policy_pdf_path)
    print(f"  {len(policy_text)} chars extracted")

    retrieval = RetrievalAgent()
    diff_agent = DiffAgent()
    impact_agent = ImpactAgent()
    verifier = VerifierAgent()

    diffs = []
    all_findings = []

    for topic in TOPICS:
        print(f"\n[{topic}]")
        ctx = retrieval.get_context(topic)
        print(f"  retrieved: {len(ctx['current'])} current, {len(ctx['repealed'])} repealed chunks")

        d = diff_agent.diff(topic, ctx["current"], ctx["repealed"])
        diffs.append(d)
        print("  diff done")

        findings = impact_agent.assess(topic, ctx["current"], policy_text)
        print(f"  impact assessment: {len(findings)} raw finding(s)")
        all_findings.extend(findings)

    print(f"\nVerifying {len(all_findings)} total findings...")
    verified = verifier.verify(all_findings)
    dropped = len(all_findings) - len(verified)
    print(f"  {len(verified)} verified, {dropped} dropped (ungrounded/uncited)")

    report = compile_report(circular_ref, diffs, verified, dropped)
    return report


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    ROOT = Path(__file__).resolve().parents[3]
    policy_path = ROOT / "data" / "policies" / "FinTrust_Digital_Lending_Policy_v2.1.pdf"
    out_path = ROOT / "evals" / "phase5_sample_memo.md"

    report = run_full_analysis("RBI/2025-26/36", str(policy_path))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"\n\nReport saved -> {out_path}")
    print("\n" + "=" * 60)
    print(report)
