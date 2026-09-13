"""
LangGraph orchestration for the 6-agent pipeline, with a human-in-the-loop
(HITL) approval gate via LangGraph's native `interrupt()`.

State is a typed dict updated node-by-node, saved by a checkpointer after
each step -- so a run can resume from a `thread_id` after a crash or while
waiting on human approval, and a follow-up question can re-run just the
node(s) it needs instead of the whole graph.

Graph shape:
  START -> process_topics (all topics concurrently)
        -> verify (Verifier Agent, all raw findings together)
        -> report (Report Agent, deterministic templating)
        -> human_approval (interrupt() -- pauses for approve/reject)
        -> finalize (approved -> output_guardrails re-check; rejected -> withheld)
        -> END
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import TypedDict


def _ts() -> str:
    """[HH:MM:SS] prefix for progress logs -- lets you see the run is alive vs stuck."""
    return datetime.now().strftime("%H:%M:%S")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "documents"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "retrieval"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
# backend/ root -- so `app.guardrails...` resolves as the same package main.py
# uses, not a second flat-imported module identity (would break isinstance
# checks on OutputGuardrailViolation in FastAPI's exception handler).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt

from app.core.config import get_settings
from app.guardrails.output_guardrails import OutputGuardrailViolation, validate_report

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


class AnalysisState(TypedDict):
    circular_ref: str
    policy_text: str
    topics: list[str]
    diffs: list[dict]
    raw_findings: list[dict]
    verified_findings: list[dict]
    report: str
    approval_status: str  # "pending" | "approved" | "rejected"
    approval_feedback: str


# Module-level singletons -- built once, not re-initialized on every node call.
_retrieval = None
_diff_agent = None
_impact_agent = None
_verifier = None


def _agents():
    global _retrieval, _diff_agent, _impact_agent, _verifier
    if _retrieval is None:
        _retrieval = RetrievalAgent()
        _diff_agent = DiffAgent()
        _impact_agent = ImpactAgent()
        _verifier = VerifierAgent()
    return _retrieval, _diff_agent, _impact_agent, _verifier


# Biggest speed win in the pipeline: topics are fully independent (different
# chunks, no shared state), but used to run one at a time -- ~945s of a
# 16m26s production run was pure sequential waiting. Now run concurrently;
# a mid-run retry already redid every topic from scratch either way, so
# this loses no resilience. 6 = all topics at once, up to 12 concurrent
# LLM calls (diff+impact x 6); NVIDIA's tier is credit-pool, not per-minute.
TOPIC_CONCURRENCY = 6


def process_topics_node(state: AnalysisState) -> dict:
    """Saare topics ek saath process karta hai (pehle ek-ek karke hote the).
    Har topic ke andar diff+impact abhi bhi parallel hain (jaisa pehle se
    tha) -- ab bas topics khud bhi ek doosre ka wait nahi karte."""
    retrieval, diff_agent, impact_agent, _ = _agents()
    topics = state["topics"]
    total = len(topics)
    print(f"\n[{_ts()}] Processing all {total} topics concurrently (up to {TOPIC_CONCURRENCY} at a time)...")

    def _process_one(item: tuple[int, str]) -> tuple[int, dict, list[dict]]:
        idx, topic = item
        print(f"[{_ts()}] [Topic {idx + 1}/{total}] {topic} -- retrieving context...")
        ctx = retrieval.get_context(topic)
        print(
            f"[{_ts()}] [Topic {idx + 1}/{total}]   retrieved: {len(ctx['current'])} current, "
            f"{len(ctx['repealed'])} repealed chunks -- calling LLM (diff + impact, in parallel)..."
        )
        t0 = time.monotonic()
        with ThreadPoolExecutor(max_workers=2) as ex:
            diff_future = ex.submit(diff_agent.diff, topic, ctx["current"], ctx["repealed"])
            impact_future = ex.submit(impact_agent.assess, topic, ctx["current"], state["policy_text"])
            d = diff_future.result()
            findings = impact_future.result()
        elapsed = time.monotonic() - t0
        print(f"[{_ts()}] [Topic {idx + 1}/{total}]   done ({elapsed:.0f}s): {len(findings)} raw finding(s)")
        return idx, d, findings

    results: list[tuple[dict, list[dict]] | None] = [None] * total
    t_all = time.monotonic()
    with ThreadPoolExecutor(max_workers=TOPIC_CONCURRENCY) as ex:
        for idx, d, findings in ex.map(_process_one, enumerate(topics)):
            results[idx] = (d, findings)

    diffs = [r[0] for r in results if r is not None]
    raw_findings = [f for r in results if r is not None for f in r[1]]
    print(
        f"[{_ts()}] All {total} topics done ({time.monotonic() - t_all:.0f}s total). "
        f"{len(raw_findings)} raw finding(s)."
    )
    return {"diffs": diffs, "raw_findings": raw_findings}


def verify_node(state: AnalysisState) -> dict:
    _, _, _, verifier = _agents()
    # Per-finding progress prints inside VerifierAgent.verify -- this used to be
    # the longest silent stretch in a run, which read as "stuck".
    print(f"\n[{_ts()}] All topics done. Verifying {len(state['raw_findings'])} total findings...")
    t0 = time.monotonic()
    verified = verifier.verify(state["raw_findings"])
    dropped = len(state["raw_findings"]) - len(verified)
    print(f"[{_ts()}]   verification done ({time.monotonic() - t0:.0f}s): {len(verified)} verified, {dropped} dropped (ungrounded/uncited)")
    return {"verified_findings": verified}


def report_node(state: AnalysisState) -> dict:
    print(f"[{_ts()}] Compiling report...")
    dropped = len(state["raw_findings"]) - len(state["verified_findings"])
    report = compile_report(state["circular_ref"], state["diffs"], state["verified_findings"], dropped)
    print(f"[{_ts()}] Report ready -- awaiting human approval.")
    return {"report": report, "approval_status": "pending"}


def human_approval_node(state: AnalysisState) -> dict:
    """Pauses here until a Command(resume=...) is sent back with a decision --
    the payload below is what the compliance officer's review screen shows."""
    decision = interrupt(
        {
            "type": "approval_required",
            "circular_ref": state["circular_ref"],
            "report": state["report"],
            "verified_findings_count": len(state["verified_findings"]),
            "question": "Approve this compliance report for delivery?",
        }
    )
    # Expected shape: {"status": "approved"} or {"status": "rejected", "feedback": "..."}
    status = decision.get("status", "rejected") if isinstance(decision, dict) else "rejected"
    feedback = decision.get("feedback", "") if isinstance(decision, dict) else ""
    return {"approval_status": status, "approval_feedback": feedback}


def finalize_node(state: AnalysisState) -> dict:
    if state["approval_status"] != "approved":
        rejected_note = (
            f"[REPORT NOT APPROVED FOR DELIVERY]\n\n"
            f"Status: {state['approval_status']}\n"
            f"Feedback: {state.get('approval_feedback') or '(none given)'}\n\n"
            f"--- Draft (not delivered) ---\n{state['report']}"
        )
        return {"report": rejected_note}

    # Last safety net -- an independent non-LLM re-check; blocks delivery even
    # if a human already approved.
    try:
        validated = validate_report(state["report"], state["verified_findings"])
        return {"report": validated}
    except OutputGuardrailViolation as e:
        blocked_note = (
            f"[BLOCKED BY OUTPUT GUARDRAIL — code={e.code}]\n{e.reason}\n\n"
            f"--- Draft (blocked, not delivered) ---\n{state['report']}"
        )
        return {"report": blocked_note}


# Module-level singleton: one ConnectionPool + PostgresSaver reused across
# the process. `.setup()` is idempotent, so it's safe to only run once.
_checkpointer = None


def _get_checkpointer():
    """PostgresSaver when DATABASE_URL is Postgres (real cross-process resume
    -- start in one process, approve in another); MemorySaver otherwise
    (dev fallback, single-process only). Uses a ConnectionPool rather than a
    single connection since FastAPI serves concurrent requests. Verified
    against a real local Postgres: pause at interrupt, resume from a
    separately compiled graph object -- state genuinely lives in Postgres."""
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    settings = get_settings()
    if settings.database_url.startswith("postgresql"):
        import psycopg
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg_pool import ConnectionPool

        pool = ConnectionPool(
            conninfo=settings.database_url,
            max_size=10,
            kwargs={"autocommit": True, "row_factory": psycopg.rows.dict_row},
            open=True,
        )
        saver = PostgresSaver(pool)
        saver.setup()
        _checkpointer = saver
    else:
        _checkpointer = MemorySaver()
    return _checkpointer


def build_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("process_topics", process_topics_node)
    graph.add_node("verify", verify_node)
    graph.add_node("report", report_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("process_topics")
    graph.add_edge("process_topics", "verify")
    graph.add_edge("verify", "report")
    graph.add_edge("report", "human_approval")
    graph.add_edge("human_approval", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=_get_checkpointer())


def start_analysis(circular_ref: str, policy_pdf_path: str, thread_id: str = "default") -> dict:
    """Runs the graph up to the human_approval interrupt; returns the
    approval-request payload, not the full report, until it's approved."""
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "documents"))
    from parser import extract_text

    print(f"\n[{_ts()}] === Starting analysis: {circular_ref} (thread {thread_id}) ===")
    print(f"[{_ts()}] Loading policy from {policy_pdf_path}...")
    policy_text = extract_text(policy_pdf_path)
    print(f"[{_ts()}]   {len(policy_text)} chars extracted")
    print(f"[{_ts()}] {len(TOPICS)} topics to process (diff + impact per topic, all topics concurrently), then verification, then report.")

    app = build_graph()
    initial_state: AnalysisState = {
        "circular_ref": circular_ref,
        "policy_text": policy_text,
        "topics": TOPICS,
        "diffs": [],
        "raw_findings": [],
        "verified_findings": [],
        "report": "",
        "approval_status": "pending",
        "approval_feedback": "",
    }
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(initial_state, config=config)
    return {"thread_id": thread_id, "state": result}


def resume_analysis(thread_id: str, approved: bool, feedback: str = "") -> dict:
    """Resumes a previously interrupted analysis. `build_graph()` builds a new
    StateGraph object, but the actual state lives in the Postgres checkpointer
    keyed by thread_id -- so this can run in any process (a different FastAPI
    or RQ worker) as long as it's the same Postgres. With MemorySaver this
    needed an in-process registry instead; removed once Postgres was wired in."""
    app = build_graph()
    config = {"configurable": {"thread_id": thread_id}}
    decision = {"status": "approved" if approved else "rejected", "feedback": feedback}
    result = app.invoke(Command(resume=decision), config=config)
    return result


# Backward-compat wrapper for evals -- runs the full pipeline in one call,
# auto-approving. Real usage calls start_analysis + resume_analysis separately.
def run_full_analysis(circular_ref: str, policy_pdf_path: str, thread_id: str = "default") -> str:
    start_analysis(circular_ref, policy_pdf_path, thread_id=thread_id)
    final_state = resume_analysis(thread_id, approved=True)
    return final_state["report"]


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    ROOT = Path(__file__).resolve().parents[3]
    policy_path = ROOT / "data" / "policies" / "FinTrust_Digital_Lending_Policy_v2.1.pdf"
    out_path = ROOT / "evals" / "phase9_hitl_memo.md"

    print("=== Phase 9 demo: start_analysis (runs until human_approval interrupt) ===")
    started = start_analysis("RBI/2025-26/36", str(policy_path))
    interrupt_payload = started["state"].get("__interrupt__")
    print("\nGraph paused for approval. Interrupt payload:")
    print(interrupt_payload)

    print("\n=== Simulating human APPROVAL and resuming ===")
    final_state = resume_analysis(started["thread_id"], approved=True)
    report = final_state["report"]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"\n\nReport saved -> {out_path}")
    print("\n" + "=" * 60)
    print(report)
