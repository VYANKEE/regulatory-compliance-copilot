"""
Analysis endpoints -- wraps the LangGraph pipeline (agents/graph.py:
start_analysis / resume_analysis) behind HTTP.

No in-process registry of compiled graph objects (there used to be one, back
when the checkpointer was MemorySaver). Now that it's Postgres-backed,
resume_analysis(thread_id, ...) can be called from any process/worker, since
the paused state lives in Postgres, not Python memory -- see graph.py's
_get_checkpointer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "app" / "agents"))

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.metrics import approval_decisions_total
from ...db import models
from ...db.session import get_db
# Dotted package import on purpose -- main.py's exception handler is
# registered against this exact class object; a flat import would create a
# second class with the same name and break isinstance checks (same bug
# class already hit once for OutputGuardrailViolation, see graph.py).
from ...guardrails.input_guardrails import GuardrailViolation, validate_query
from ...schemas.analysis import (
    ApprovalRequest,
    AskRequest,
    AskResponse,
    StartAnalysisRequest,
    StartAnalysisResponse,
    ThreadOut,
    ThreadSummary,
)
from ..deps import enforce_rate_limit, get_current_user

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/start", response_model=StartAnalysisResponse)
def start(
    req: StartAnalysisRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    _rl: None = Depends(enforce_rate_limit),
):
    """Enqueues the analysis rather than running the pipeline inline -- the
    real work happens in an RQ background worker (jobs/worker.py). Returns
    fast with status "pending"; the client polls GET /analysis/{thread_id}
    until "awaiting_approval" or "failed"."""
    policy_doc = db.get(models.PolicyDocument, req.policy_document_id)
    if policy_doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="policy_document_id not found")

    thread = models.AnalysisThread(
        user_id=user.id,
        circular_ref=req.circular_ref,
        policy_document_id=req.policy_document_id,
        status="pending",
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)

    db.add(models.AuditLog(user_id=user.id, thread_id=thread.id, action="analysis_started", detail=req.circular_ref))
    db.commit()

    from rq import Retry

    from ...jobs.queue import get_queue
    from ...jobs.tasks import run_analysis_job

    # NVIDIA's free tier occasionally 503s for several minutes -- long enough
    # to exhaust the per-call retry budget inside the agents. Retry(max=2,
    # interval=[120, 300]) re-runs the whole job if it still fails, giving
    # the provider time to recover (see jobs/tasks.py: status is only marked
    # "failed" on the genuinely final attempt). job_timeout=3600 gives real
    # headroom for a normal run's many LLM calls without being unbounded.
    get_queue().enqueue(
        run_analysis_job,
        thread.id,
        req.circular_ref,
        policy_doc.storage_path,
        job_timeout=3600,
        retry=Retry(max=2, interval=[120, 300]),
    )

    return StartAnalysisResponse(
        thread_id=thread.id,
        status=thread.status,
        approval_pending=False,
        draft_report=None,
        verified_findings_count=None,
    )


@router.post("/{thread_id}/approve", response_model=ThreadOut)
def approve(
    thread_id: str,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    _rl: None = Depends(enforce_rate_limit),
):
    import graph as graph_module

    thread = db.get(models.AnalysisThread, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="thread not found")
    if thread.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not your thread")

    if thread.status != "awaiting_approval":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This analysis is not awaiting approval (current status: {thread.status}).",
        )

    final_state = graph_module.resume_analysis(thread_id, approved=req.approved, feedback=req.feedback)
    approval_decisions_total.labels("approved" if req.approved else "rejected").inc()

    db.add(
        models.ApprovalDecision(
            thread_id=thread_id,
            decided_by=user.id,
            status="approved" if req.approved else "rejected",
            feedback=req.feedback,
        )
    )

    thread.status = "completed" if req.approved else "rejected"
    thread.report = final_state["report"]
    db.commit()

    if req.approved:
        for f in final_state.get("verified_findings", []):
            db.add(
                models.Finding(
                    thread_id=thread_id,
                    requirement=f.get("requirement", ""),
                    status=f.get("status", ""),
                    rbi_citation=f.get("rbi_citation", ""),
                    explanation=f.get("explanation", ""),
                    suggested_policy_change=f.get("suggested_policy_change", ""),
                )
            )
        db.commit()

    db.add(
        models.AuditLog(
            user_id=user.id,
            thread_id=thread_id,
            action="report_approved" if req.approved else "report_rejected",
            detail=req.feedback,
        )
    )
    db.commit()
    db.refresh(thread)
    return thread


@router.get("/", response_model=list[ThreadSummary])
def list_threads(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Dashboard listing -- this user's threads, newest first, summary only
    (full detail is GET /analysis/{thread_id})."""
    threads = (
        db.query(models.AnalysisThread)
        .filter(models.AnalysisThread.user_id == user.id)
        .order_by(models.AnalysisThread.created_at.desc())
        .all()
    )
    return threads


@router.get("/{thread_id}", response_model=ThreadOut)
def get_thread(
    thread_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    thread = db.get(models.AnalysisThread, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="thread not found")
    if thread.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not your thread")
    return thread


@router.post("/{thread_id}/ask", response_model=AskResponse)
def ask_followup(
    thread_id: str,
    req: AskRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    _rl: None = Depends(enforce_rate_limit),
):
    """Grounded follow-up Q&A on an analysis -- see agents/followup_agent.py.
    Works regardless of thread status (a reviewer may ask before or after
    approval). Each call is independent -- no conversation-history table;
    the frontend keeps that in its own state."""
    thread = db.get(models.AnalysisThread, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="thread not found")
    if thread.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not your thread")

    # Same cheap, non-LLM input guardrail every user-text entry point uses.
    question = validate_query(req.question)

    import followup_agent as followup_module

    agent = followup_module.FollowUpAgent()
    findings = [
        {
            "requirement": f.requirement,
            "status": f.status,
            "rbi_citation": f.rbi_citation,
            "explanation": f.explanation,
        }
        for f in thread.findings
    ]
    result = agent.ask(question, thread.circular_ref, findings)

    db.add(
        models.AuditLog(
            user_id=user.id,
            thread_id=thread_id,
            action="followup_asked",
            detail=question[:200],
        )
    )
    db.commit()

    return AskResponse(**result)


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(
    thread_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Deletes an analysis. Findings/approvals cascade-delete (models.py).
    AuditLog rows are kept for the audit trail -- their thread_id is set to
    NULL instead, since there's no ON DELETE CASCADE FK on them."""
    thread = db.get(models.AnalysisThread, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="thread not found")
    if thread.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not your thread")

    db.query(models.AuditLog).filter(models.AuditLog.thread_id == thread_id).update({"thread_id": None})
    db.delete(thread)
    db.commit()
