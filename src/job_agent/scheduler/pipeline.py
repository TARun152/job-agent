"""Discover → score → tailor → enqueue pipeline used by CLI and scheduler."""

from __future__ import annotations

from job_agent.config import Settings, get_settings
from job_agent.constants.statuses import (
    JOB_STATUS_MATCHED,
    JOB_STATUS_SKIPPED_LOW_SCORE,
    JOB_STATUS_TAILORED,
)
from job_agent.db.repository import enqueue_application, update_job_match, upsert_job
from job_agent.db.session import init_db, session_scope
from job_agent.logging_setup import configure_logging, get_logger
from job_agent.matcher.scorer import score_job_against_profile
from job_agent.resume.parser import load_profile_from_resume_dir
from job_agent.sources import (
    InstahyreSource,
    LinkedInSource,
    NaukriSource,
    WorkdaySource,
    discover_all,
)
from job_agent.tailor.rewriter import tailor_resume_for_job

pclog = get_logger(__name__)


def run_discover_match_tailor_enqueue(settings: Settings | None = None) -> dict[str, int]:
    """Run one full discovery pipeline cycle.

    Args:
        settings: Optional settings override.

    Returns:
        Counts dict: discovered, matched, tailored, enqueued, skipped.
    """
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    init_db()
    settings.ensure_runtime_dirs()

    pclog.info("Pipeline start env=%s", settings.job_agent_env)
    # Parse the uploaded resume once for the whole cycle.
    profile = load_profile_from_resume_dir(
        settings.resume_dir, notice_period_days=settings.notice_period_days
    )

    sources = [NaukriSource(), InstahyreSource(), LinkedInSource(), WorkdaySource()]
    limit = max(1, settings.max_daily_discoveries // max(len(sources), 1))
    jobs = discover_all(
        sources,
        keywords=settings.role_keyword_list(),
        locations=settings.location_list(),
        limit_per_source=limit,
    )

    counts = {
        "discovered": len(jobs),
        "matched": 0,
        "tailored": 0,
        "enqueued": 0,
        "skipped": 0,
    }

    with session_scope() as session:
        for job in jobs:
            # Persist discovery row (idempotent on portal+external_id).
            record = upsert_job(session, job)
            match = score_job_against_profile(
                job=job,
                profile=profile,
                role_keywords=settings.role_keyword_list(),
                locations=settings.location_list(),
                remote_ok=settings.remote_ok,
                openai_api_key=settings.openai_api_key,
                embedding_model=settings.embedding_model,
            )
            if match.score < settings.match_score_threshold:
                update_job_match(
                    session,
                    record.id,
                    match.score,
                    match.rationale,
                    JOB_STATUS_SKIPPED_LOW_SCORE,
                )
                counts["skipped"] += 1
                continue

            update_job_match(
                session,
                record.id,
                match.score,
                match.rationale,
                JOB_STATUS_MATCHED,
            )
            counts["matched"] += 1

            # Produce tailored PDF + diff for human review.
            tailored = tailor_resume_for_job(
                profile=profile,
                job=job,
                output_dir=settings.tailored_dir,
                keyword_stuff_cap=settings.match_keyword_stuff_cap,
            )
            update_job_match(
                session,
                record.id,
                match.score,
                match.rationale,
                JOB_STATUS_TAILORED,
            )
            counts["tailored"] += 1

            app = enqueue_application(
                session,
                job_id=record.id,
                tailored_pdf_path=str(tailored.pdf_path),
                diff_path=str(tailored.diff_path),
                diff_text=tailored.diff_text,
            )
            if app is not None:
                counts["enqueued"] += 1

    pclog.info("Pipeline complete counts=%s", counts)
    return counts
