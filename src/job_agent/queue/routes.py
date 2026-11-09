"""HTTP routes for the approval queue UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from job_agent.apply.registry import get_apply_adapter
from job_agent.config import get_settings
from job_agent.constants.statuses import APP_STATUS_APPROVED, APP_STATUS_QUEUED, APP_STATUS_SKIPPED
from job_agent.db.repository import (
    count_applies_today,
    get_application_with_job,
    list_queued_applications,
    mark_application_status,
)
from job_agent.db.session import session_scope
from job_agent.logging_setup import get_logger
from job_agent.models.job import Job
from job_agent.resume.parser import load_profile_from_resume_dir

pclog = get_logger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/", response_class=HTMLResponse)
def queue_home(request: Request) -> HTMLResponse:
    """Render the approval queue list.

    Args:
        request: Incoming FastAPI request.

    Returns:
        HTML page with queued applications.
    """
    with session_scope() as session:
        rows = list_queued_applications(session)
        applies_today = count_applies_today(session)
        items = [
            {
                "app_id": app.id,
                "title": job.title,
                "company": job.company,
                "portal": job.portal,
                "location": job.location,
                "score": job.match_score,
                "rationale": job.match_rationale,
                "url": job.url,
                "diff_text": app.diff_text,
                "pause_reason": app.pause_reason,
            }
            for app, job in rows
        ]
    pclog.info("Rendered queue home items=%s", len(items))
    return templates.TemplateResponse(
        request,
        "queue.html",
        {
            "items": items,
            "applies_today": applies_today,
            "max_daily_applies": get_settings().max_daily_applies,
        },
    )


@router.post("/applications/{app_id}/approve")
def approve_application(app_id: int) -> RedirectResponse:
    """Approve a queued application and trigger portal apply.

    Args:
        app_id: Application primary key.

    Returns:
        Redirect back to the queue home.
    """
    settings = get_settings()
    pclog.info("Approve requested app_id=%s", app_id)

    job_model: Job | None = None
    tailored_pdf_path = ""
    with session_scope() as session:
        if count_applies_today(session) >= settings.max_daily_applies:
            pclog.warning("Daily apply cap reached app_id=%s", app_id)
            mark_application_status(
                session,
                app_id,
                status=APP_STATUS_QUEUED,
                apply_notes="Daily apply cap reached; left queued.",
            )
            return RedirectResponse(url="/", status_code=303)

        pair = get_application_with_job(session, app_id)
        if pair is None:
            pclog.warning("Approve missed app_id=%s", app_id)
            return RedirectResponse(url="/", status_code=303)
        app, job = pair
        # Copy values out before the session closes.
        job_model = job.to_job()
        tailored_pdf_path = app.tailored_pdf_path
        mark_application_status(session, app_id, status=APP_STATUS_APPROVED)

    try:
        # Load resume profile for screening answers and apply forms.
        profile = load_profile_from_resume_dir(
            settings.resume_dir, notice_period_days=settings.notice_period_days
        )
    except FileNotFoundError as exc:
        with session_scope() as session:
            mark_application_status(
                session,
                app_id,
                status=APP_STATUS_APPROVED,
                apply_notes=str(exc),
            )
        return RedirectResponse(url="/", status_code=303)

    assert job_model is not None
    adapter = get_apply_adapter(job_model.portal)
    result = adapter.apply(job_model, profile, tailored_pdf_path)
    with session_scope() as session:
        mark_application_status(
            session,
            app_id,
            status=APP_STATUS_APPROVED,
            apply_status=result.status,
            pause_reason=result.pause_reason,
            apply_notes=result.notes,
        )
    pclog.info("Approve finished app_id=%s apply_status=%s", app_id, result.status)
    return RedirectResponse(url="/", status_code=303)


@router.post("/applications/{app_id}/skip")
def skip_application(app_id: int, reason: str = Form(default="")) -> RedirectResponse:
    """Skip a queued application without applying.

    Args:
        app_id: Application primary key.
        reason: Optional skip reason from the form.

    Returns:
        Redirect back to the queue home.
    """
    with session_scope() as session:
        mark_application_status(
            session,
            app_id,
            status=APP_STATUS_SKIPPED,
            apply_notes=reason or "Skipped by user",
        )
    pclog.info("Skipped application app_id=%s", app_id)
    return RedirectResponse(url="/", status_code=303)


@router.get("/applications/{app_id}/pdf")
def download_tailored_pdf(app_id: int):
    """Download the tailored PDF for an application.

    Args:
        app_id: Application primary key.

    Returns:
        File response or redirect when missing.
    """
    with session_scope() as session:
        pair = get_application_with_job(session, app_id)
        if pair is None:
            return RedirectResponse(url="/", status_code=303)
        app, _job = pair
        path = Path(app.tailored_pdf_path)
    if not path.exists():
        pclog.warning("Tailored PDF missing app_id=%s path=%s", app_id, path)
        return RedirectResponse(url="/", status_code=303)
    return FileResponse(path, filename=path.name, media_type="application/pdf")
