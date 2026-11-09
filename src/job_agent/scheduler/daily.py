"""APScheduler wrapper for the daily pipeline."""

from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from job_agent.config import get_settings
from job_agent.constants.scheduler_const import DAILY_PIPELINE_CRON_HOUR, DAILY_PIPELINE_CRON_MINUTE
from job_agent.logging_setup import configure_logging, get_logger
from job_agent.scheduler.pipeline import run_discover_match_tailor_enqueue

pclog = get_logger(__name__)


def run_daily_pipeline() -> dict[str, int]:
    """Execute one daily discover/match/tailor/enqueue cycle.

    Returns:
        Pipeline counts dictionary.
    """
    settings = get_settings()
    configure_logging(settings.log_level)
    pclog.info("Daily pipeline triggered")
    # Delegate to the shared pipeline implementation.
    return run_discover_match_tailor_enqueue(settings)


def start_scheduler() -> None:
    """Start a blocking scheduler that runs the pipeline once daily.

    Uses local timezone hour/minute constants. Blocks the current thread.
    """
    settings = get_settings()
    configure_logging(settings.log_level)
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_daily_pipeline,
        trigger="cron",
        hour=DAILY_PIPELINE_CRON_HOUR,
        minute=DAILY_PIPELINE_CRON_MINUTE,
        id="daily_job_agent_pipeline",
        replace_existing=True,
    )
    pclog.info(
        "Scheduler started daily_at=%02d:%02d",
        DAILY_PIPELINE_CRON_HOUR,
        DAILY_PIPELINE_CRON_MINUTE,
    )
    # Run once immediately so first-time setup has data without waiting for cron.
    run_daily_pipeline()
    scheduler.start()
