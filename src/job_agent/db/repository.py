"""CRUD helpers for jobs and applications."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from job_agent.constants.apply import APPLY_STATUS_APPLIED, APPLY_STATUS_PENDING
from job_agent.constants.statuses import (
    APP_STATUS_APPROVED,
    APP_STATUS_QUEUED,
    APP_STATUS_SKIPPED,
    JOB_STATUS_DISCOVERED,
)
from job_agent.logging_setup import get_logger
from job_agent.models.application import ApplicationRecord
from job_agent.models.job import Job, JobRecord

pclog = get_logger(__name__)


def upsert_job(session: Session, job: Job) -> JobRecord:
    """Insert a discovered job or return the existing portal/external row.

    Args:
        session: Active DB session.
        job: Normalized job from a portal adapter.

    Returns:
        Persisted ``JobRecord``.
    """
    # Look up by portal + external id to avoid duplicate discoveries.
    existing = session.scalar(
        select(JobRecord).where(
            JobRecord.portal == job.portal,
            JobRecord.external_id == job.external_id,
        )
    )
    if existing:
        pclog.debug(
            "Job already stored portal=%s external_id=%s id=%s",
            job.portal,
            job.external_id,
            existing.id,
        )
        return existing

    record = JobRecord(
        external_id=job.external_id,
        portal=job.portal,
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        url=job.url,
        salary_text=job.salary_text,
        posted_at=job.posted_at,
        is_remote=job.is_remote,
        status=JOB_STATUS_DISCOVERED,
    )
    session.add(record)
    session.flush()
    pclog.info(
        "Stored job id=%s portal=%s title=%s company=%s",
        record.id,
        record.portal,
        record.title,
        record.company,
    )
    return record


def update_job_match(
    session: Session,
    job_id: int,
    score: float,
    rationale: str,
    status: str,
) -> JobRecord | None:
    """Persist match score and status on a job row.

    Args:
        session: Active DB session.
        job_id: Primary key of the job.
        score: Match score in ``[0, 1]``.
        rationale: Short human-readable reason.
        status: New job lifecycle status.

    Returns:
        Updated ``JobRecord``, or ``None`` if missing.
    """
    record = session.get(JobRecord, job_id)
    if record is None:
        pclog.warning("Cannot update match; job_id=%s not found", job_id)
        return None
    record.match_score = score
    record.match_rationale = rationale
    record.status = status
    session.flush()
    pclog.info("Updated match job_id=%s score=%.3f status=%s", job_id, score, status)
    return record


def enqueue_application(
    session: Session,
    job_id: int,
    tailored_pdf_path: str,
    diff_path: str,
    diff_text: str,
) -> ApplicationRecord:
    """Create a queued application for human approval.

    Args:
        session: Active DB session.
        job_id: Linked job primary key.
        tailored_pdf_path: Path to tailored PDF.
        diff_path: Path to saved diff file.
        diff_text: Inline diff for the approval UI.

    Returns:
        New ``ApplicationRecord`` in queued status.
    """
    existing = session.scalar(select(ApplicationRecord).where(ApplicationRecord.job_id == job_id))
    if existing:
        pclog.debug("Application already queued for job_id=%s app_id=%s", job_id, existing.id)
        return existing

    app = ApplicationRecord(
        job_id=job_id,
        status=APP_STATUS_QUEUED,
        apply_status=APPLY_STATUS_PENDING,
        tailored_pdf_path=tailored_pdf_path,
        diff_path=diff_path,
        diff_text=diff_text,
    )
    session.add(app)
    session.flush()
    pclog.info("Enqueued application id=%s job_id=%s", app.id, job_id)
    return app


def list_queued_applications(session: Session) -> list[tuple[ApplicationRecord, JobRecord]]:
    """Return queued applications joined with their jobs, newest first.

    Args:
        session: Active DB session.

    Returns:
        List of ``(application, job)`` tuples.
    """
    stmt: Select = (
        select(ApplicationRecord, JobRecord)
        .join(JobRecord, ApplicationRecord.job_id == JobRecord.id)
        .where(ApplicationRecord.status == APP_STATUS_QUEUED)
        .order_by(ApplicationRecord.created_at.desc())
    )
    rows = list(session.execute(stmt).all())
    pclog.debug("Listed queued applications count=%s", len(rows))
    return [(app, job) for app, job in rows]


def get_application_with_job(
    session: Session, app_id: int
) -> tuple[ApplicationRecord, JobRecord] | None:
    """Load one application and its job by application id.

    Args:
        session: Active DB session.
        app_id: Application primary key.

    Returns:
        ``(application, job)`` or ``None``.
    """
    stmt = (
        select(ApplicationRecord, JobRecord)
        .join(JobRecord, ApplicationRecord.job_id == JobRecord.id)
        .where(ApplicationRecord.id == app_id)
    )
    row = session.execute(stmt).first()
    if row is None:
        return None
    return row[0], row[1]


def mark_application_status(
    session: Session,
    app_id: int,
    status: str,
    apply_status: str | None = None,
    pause_reason: str = "",
    apply_notes: str = "",
) -> ApplicationRecord | None:
    """Update approval or apply status fields on an application.

    Args:
        session: Active DB session.
        app_id: Application primary key.
        status: New approval-queue status.
        apply_status: Optional apply-pipeline status.
        pause_reason: CAPTCHA/2FA note when paused.
        apply_notes: Free-form apply outcome notes.

    Returns:
        Updated record, or ``None`` if missing.
    """
    app = session.get(ApplicationRecord, app_id)
    if app is None:
        pclog.warning("Application not found app_id=%s", app_id)
        return None
    app.status = status
    if apply_status is not None:
        app.apply_status = apply_status
    if pause_reason:
        app.pause_reason = pause_reason
    if apply_notes:
        app.apply_notes = apply_notes
    now = datetime.now(UTC)
    if status == APP_STATUS_APPROVED:
        app.approved_at = now
    if apply_status == APPLY_STATUS_APPLIED:
        app.applied_at = now
    if status == APP_STATUS_SKIPPED:
        app.apply_status = apply_status or APP_STATUS_SKIPPED
    session.flush()
    pclog.info(
        "Updated application app_id=%s status=%s apply_status=%s",
        app_id,
        app.status,
        app.apply_status,
    )
    return app


def count_applies_today(session: Session) -> int:
    """Count applications marked applied since UTC midnight.

    Args:
        session: Active DB session.

    Returns:
        Number of applies today.
    """
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    count = session.scalar(
        select(func.count())
        .select_from(ApplicationRecord)
        .where(
            ApplicationRecord.apply_status == APPLY_STATUS_APPLIED,
            ApplicationRecord.applied_at >= start,
        )
    )
    return int(count or 0)
