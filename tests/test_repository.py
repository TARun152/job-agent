"""Unit tests for SQLite repository helpers."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from job_agent.constants.statuses import APP_STATUS_QUEUED, JOB_STATUS_MATCHED
from job_agent.db.base import Base
from job_agent.db.repository import enqueue_application, update_job_match, upsert_job
from job_agent.models.application import ApplicationRecord  # noqa: F401
from job_agent.models.job import Job, JobRecord  # noqa: F401


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_upsert_job_is_idempotent() -> None:
    session = _session()
    job = Job(
        external_id="abc",
        portal="naukri",
        title="AI Engineer",
        company="X",
        description="Python RAG",
    )
    first = upsert_job(session, job)
    second = upsert_job(session, job)
    assert first.id == second.id
    session.close()


def test_enqueue_application_and_match_update() -> None:
    session = _session()
    job = Job(external_id="xyz", portal="instahyre", title="NLP Engineer", company="Y")
    record = upsert_job(session, job)
    update_job_match(session, record.id, 0.8, "skills ok", JOB_STATUS_MATCHED)
    app = enqueue_application(
        session,
        job_id=record.id,
        tailored_pdf_path="/tmp/a.pdf",
        diff_path="/tmp/a.diff.txt",
        diff_text="+ hello",
    )
    again = enqueue_application(
        session,
        job_id=record.id,
        tailored_pdf_path="/tmp/a.pdf",
        diff_path="/tmp/a.diff.txt",
        diff_text="+ hello",
    )
    assert app.id == again.id
    assert app.status == APP_STATUS_QUEUED
    refreshed = session.get(JobRecord, record.id)
    assert refreshed is not None
    assert refreshed.match_score == 0.8
    session.close()
