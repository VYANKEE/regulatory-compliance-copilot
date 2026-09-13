"""
ORM models. SQLAlchemy 2.0 style (Mapped / mapped_column).

Notes: `AnalysisThread.id` deliberately matches LangGraph's `thread_id`, so
graph checkpoint state and business data (findings, approvals, audit) share
one key. `Finding` rows are only ever populated from verified_findings --
ungrounded findings never reach the DB. `AuditLog` captures every
repudiation-relevant action (who did what, when, on which thread).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    # Firebase UID is the primary key -- no need for our own user-id scheme.
    id: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    display_name: Mapped[str] = mapped_column(default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    threads: Mapped[list["AnalysisThread"]] = relationship(back_populates="user")


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    uploaded_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column()
    storage_path: Mapped[str] = mapped_column()
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AnalysisThread(Base):
    __tablename__ = "analysis_threads"

    # Same value as the LangGraph thread_id -- shared key for graph + business data.
    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    circular_ref: Mapped[str] = mapped_column()
    policy_document_id: Mapped[str] = mapped_column(ForeignKey("policy_documents.id"))
    # pending -> awaiting_approval -> approved/rejected -> completed
    status: Mapped[str] = mapped_column(default="pending")
    report: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["User"] = relationship(back_populates="threads")
    findings: Mapped[list["Finding"]] = relationship(back_populates="thread", cascade="all, delete-orphan")
    approvals: Mapped[list["ApprovalDecision"]] = relationship(back_populates="thread", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    thread_id: Mapped[str] = mapped_column(ForeignKey("analysis_threads.id"))
    requirement: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column()  # "Met" | "Not Met" | "Partial"
    rbi_citation: Mapped[str] = mapped_column()
    explanation: Mapped[str] = mapped_column(Text, default="")
    suggested_policy_change: Mapped[str] = mapped_column(Text, default="")
    # True only when the Verifier Agent independently grounded it -- unverified
    # findings never reach the DB (dropped upstream).
    verified: Mapped[bool] = mapped_column(default=True)

    thread: Mapped["AnalysisThread"] = relationship(back_populates="findings")


class ApprovalDecision(Base):
    __tablename__ = "approval_decisions"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    thread_id: Mapped[str] = mapped_column(ForeignKey("analysis_threads.id"))
    decided_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column()  # "approved" | "rejected"
    feedback: Mapped[str] = mapped_column(Text, default="")
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    thread: Mapped["AnalysisThread"] = relationship(back_populates="approvals")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    thread_id: Mapped[str | None] = mapped_column(ForeignKey("analysis_threads.id"), nullable=True)
    action: Mapped[str] = mapped_column()  # e.g. "analysis_started", "report_approved"
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
