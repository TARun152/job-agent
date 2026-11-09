"""Queued application and apply-attempt persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from job_agent.constants.apply import APPLY_STATUS_PENDING
from job_agent.constants.statuses import APP_STATUS_QUEUED
from job_agent.db.base import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class ApplicationRecord(Base):
    """One approval-queue item linked to a discovered job."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    status: Mapped[str] = mapped_column(String(64), default=APP_STATUS_QUEUED, index=True)
    apply_status: Mapped[str] = mapped_column(String(64), default=APPLY_STATUS_PENDING)
    tailored_pdf_path: Mapped[str] = mapped_column(String(1024), default="")
    diff_path: Mapped[str] = mapped_column(String(1024), default="")
    diff_text: Mapped[str] = mapped_column(Text, default="")
    pause_reason: Mapped[str] = mapped_column(Text, default="")
    apply_notes: Mapped[str] = mapped_column(Text, default="")
    gmail_thread_id: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
