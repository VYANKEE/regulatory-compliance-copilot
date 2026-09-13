"""
Background job functions -- run in an RQ worker process, not FastAPI's, so
the request-scoped get_db() dependency doesn't apply. Each job opens and
closes its own DB session.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents"))

from ..core.metrics import analyses_completed_total, analyses_failed_total, analyses_started_total, verified_findings_per_analysis
from ..db import models
from ..db.session import SessionLocal


def run_analysis_job(thread_id: str, circular_ref: str, policy_pdf_path: str) -> None:
    """Runs start_analysis() (retrieval + diff + impact for all topics) and
    updates the thread row with the result. The graph pauses itself at the
    human_approval node; this job's only responsibility is getting there --
    approval happens via a separate /analysis/{id}/approve call."""
    import graph as graph_module
    from rq import get_current_job

    analyses_started_total.inc()
    db = SessionLocal()
    try:
        thread = db.get(models.AnalysisThread, thread_id)
        if thread is None:
            return  # thread was deleted -- nothing to do

        try:
            started = graph_module.start_analysis(circular_ref, policy_pdf_path, thread_id=thread_id)
        except Exception as e:
            # NVIDIA's transient overloads can exhaust the agent-level retry
            # budget, so RQ retries the whole job too (see
            # api/routes/analysis.py's enqueue). Only mark "failed" on the
            # genuinely final attempt -- not one RQ is about to retry -- so
            # the dashboard doesn't show a wrong "failed" state.
            job = get_current_job()
            retries_left = job.retries_left if job is not None else None
            if retries_left:
                db.add(
                    models.AuditLog(
                        thread_id=thread_id,
                        action="analysis_attempt_failed_will_retry",
                        detail=f"{e} (retries left: {retries_left})",
                    )
                )
                db.commit()
                raise  # RQ re-enqueues automatically -- no "failed" mark

            analyses_failed_total.inc()
            thread.status = "failed"
            thread.report = f"Analysis failed after all retries: {e}"
            db.commit()
            db.add(models.AuditLog(thread_id=thread_id, action="analysis_failed", detail=str(e)))
            db.commit()
            raise  # propagate to RQ for dashboard/retry visibility

        thread.status = "awaiting_approval"
        thread.report = started["state"].get("report", "")
        db.commit()
        db.add(models.AuditLog(thread_id=thread_id, action="analysis_ready_for_approval"))
        db.commit()

        analyses_completed_total.inc()
        verified_findings_per_analysis.observe(len(started["state"].get("verified_findings", [])))
    finally:
        db.close()
