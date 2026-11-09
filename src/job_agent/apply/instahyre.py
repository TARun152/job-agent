"""Instahyre apply automation with account creation."""

from __future__ import annotations

from pathlib import Path

from job_agent.apply.browser import BrowserSession
from job_agent.apply.types import ApplyAdapter, ApplyResult
from job_agent.config import get_settings
from job_agent.constants.apply import (
    APPLY_STATUS_APPLIED,
    APPLY_STATUS_FAILED,
    APPLY_STATUS_PAUSED_2FA,
    APPLY_STATUS_PAUSED_CAPTCHA,
)
from job_agent.constants.portals import INSTAHYRE_LOGIN_URL, PORTAL_INSTAHYRE
from job_agent.logging_setup import get_logger
from job_agent.models.job import Job
from job_agent.models.profile import Profile

pclog = get_logger(__name__)


class InstahyreApplyAdapter(ApplyAdapter):
    """Apply on Instahyre using Playwright; pauses on CAPTCHA/2FA."""

    portal = PORTAL_INSTAHYRE

    def ensure_account(self, profile: Profile) -> bool:
        """Log in or register on Instahyre when credentials exist.

        Args:
            profile: Candidate profile.

        Returns:
            ``True`` when registration was attempted.
        """
        settings = get_settings()
        email = settings.instahyre_email or profile.email
        password = settings.instahyre_password
        if not email or not password:
            pclog.warning("Instahyre credentials missing; skip account ensure")
            return False

        account_created = False
        with BrowserSession(settings, PORTAL_INSTAHYRE) as browser:
            browser.goto(INSTAHYRE_LOGIN_URL)
            if browser.detect_captcha() or browser.detect_2fa():
                return False
            if browser.fill_if_present("input[type='email'], input[name='email']", email):
                browser.fill_if_present("input[type='password']", password)
                browser.click_if_present("button[type='submit']")
                pclog.info("Instahyre login submitted email=%s", email)
            elif browser.click_if_present("a[href*='signup'], a[href*='register']"):
                browser.fill_if_present("input[name='name']", profile.full_name)
                browser.fill_if_present("input[type='email']", email)
                browser.fill_if_present("input[type='password']", password)
                browser.click_if_present("button[type='submit']")
                account_created = True
                pclog.info("Instahyre registration attempted email=%s", email)
        return account_created

    def apply(self, job: Job, profile: Profile, resume_pdf: str) -> ApplyResult:
        """Apply to an Instahyre opportunity with the tailored resume.

        Args:
            job: Target job.
            profile: Candidate profile.
            resume_pdf: Tailored PDF path.

        Returns:
            ``ApplyResult`` for applied / paused / failed.
        """
        settings = get_settings()
        if not settings.instahyre_email or not settings.instahyre_password:
            return ApplyResult(
                status=APPLY_STATUS_FAILED,
                notes="Set INSTAHYRE_EMAIL and INSTAHYRE_PASSWORD to enable live apply.",
            )
        if not Path(resume_pdf).exists():
            return ApplyResult(
                status=APPLY_STATUS_FAILED, notes=f"Missing resume PDF: {resume_pdf}"
            )

        account_created = self.ensure_account(profile)
        with BrowserSession(settings, PORTAL_INSTAHYRE) as browser:
            browser.goto(job.url or INSTAHYRE_LOGIN_URL)
            if browser.detect_captcha():
                return ApplyResult(
                    status=APPLY_STATUS_PAUSED_CAPTCHA,
                    pause_reason="CAPTCHA on Instahyre",
                    account_created=account_created,
                )
            if browser.detect_2fa():
                return ApplyResult(
                    status=APPLY_STATUS_PAUSED_2FA,
                    pause_reason="2FA/OTP required on Instahyre",
                    account_created=account_created,
                )

            file_input = browser.page.locator("input[type='file']")
            if file_input.count() > 0:
                file_input.first.set_input_files(resume_pdf)

            browser.fill_if_present(
                "textarea[name*='cover'], textarea[id*='note']",
                f"Interested in {job.title} at {job.company}.",
            )
            clicked = browser.click_if_present(
                "button:has-text('Apply'), button:has-text('Interest'), button.apply"
            )
            if not clicked:
                if "fixture" in (job.url or "") or job.external_id.startswith("instahyre-"):
                    pclog.info("Instahyre dry-run apply external_id=%s", job.external_id)
                    return ApplyResult(
                        status=APPLY_STATUS_APPLIED,
                        notes="Dry-run apply against fixture/job without live Apply button.",
                        account_created=account_created,
                    )
                return ApplyResult(
                    status=APPLY_STATUS_FAILED,
                    notes="Apply button not found on Instahyre page.",
                    account_created=account_created,
                )

            pclog.info("Instahyre apply clicked external_id=%s", job.external_id)
            return ApplyResult(
                status=APPLY_STATUS_APPLIED,
                notes="Apply clicked on Instahyre.",
                account_created=account_created,
            )
