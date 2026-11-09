"""FastAPI application factory for the approval queue."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from job_agent.db.session import init_db
from job_agent.logging_setup import configure_logging, get_logger
from job_agent.queue.routes import router

pclog = get_logger(__name__)


def create_app() -> FastAPI:
    """Build the approval-queue FastAPI app.

    Returns:
        Configured ``FastAPI`` instance.
    """
    from job_agent.config import get_settings

    settings = get_settings()
    # Configure logging and ensure schema before serving requests.
    configure_logging(settings.log_level)
    init_db()

    app = FastAPI(title="Job Agent Approval Queue", version="0.1.0")
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.include_router(router)
    pclog.info("Approval queue app created")
    return app
