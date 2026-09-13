"""Request/response models for the analysis API. Kept separate from the ORM
models (db/models.py) so API shape and DB shape can evolve independently
(e.g. a derived field like `approval_pending` with no DB column)."""

from datetime import datetime

from pydantic import BaseModel


class StartAnalysisRequest(BaseModel):
    circular_ref: str
    policy_document_id: str


class StartAnalysisResponse(BaseModel):
    thread_id: str
    status: str
    approval_pending: bool
    # When approval_pending is True, these come from the interrupt() payload.
    draft_report: str | None = None
    verified_findings_count: int | None = None


class ApprovalRequest(BaseModel):
    approved: bool
    feedback: str = ""


class FindingOut(BaseModel):
    id: str
    requirement: str
    status: str
    rbi_citation: str
    explanation: str
    suggested_policy_change: str

    class Config:
        from_attributes = True


class ThreadOut(BaseModel):
    id: str
    circular_ref: str
    status: str
    report: str
    created_at: datetime
    updated_at: datetime
    findings: list[FindingOut] = []

    class Config:
        from_attributes = True

class ThreadSummary(BaseModel):
    id: str
    circular_ref: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    # Real chunk_ids the retrieval agent actually pulled for this question --
    # not a claim that the model cited every one, just what it was given.
    citations: list[str]
