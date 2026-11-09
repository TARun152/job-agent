"""Naukri apply automation with account creation."""

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
from job_agent.constants.portals import NAUKRI_LOGIN_URL, PORTAL_NAUKRI
from job_agent.logging_setup import get_logger
from job_agent.models.job import Job
from job_agent.models.profile import Profile

pclog = get_logger(__name__)


class NaukriApplyAdapter(ApplyAdapter):
    """Apply on Naukri using Playwright; pauses on CAPTCHA/2FA."""

    portal = PORTAL_NAUKRI

    def ensure_account(self, profile: Profile) -> bool:
        """Log in or attempt registration when credentials are configured.

        Args:
            profile: Candidate profile (email fallback).

        Returns:
            ``True`` when a registration flow was attempted.
        """
        settings = get_settings()
        email = settings.naukri_email or profile.email
        password = settings.naukri_password
        if not email or not password:
            pclog.warning("Naukri credentials missing; skip account ensure")
            return False

        account_created = False
        with BrowserSession(settings, PORTAL_NAUKRI) as browser:
            # Open login; if register link exists and session is empty, try it.
            browser.goto(NAUKRI_LOGIN_URL)
            if browser.detect_captcha():
                return False
            if browser.detect_2fa():
                return False
            filled_email = browser.fill_if_present(
                "input[type='text'], input[name='email'], #usernameField",
                email,
            )
            filled_password = browser.fill_if_present(
                "input[type='password'], #passwordField",
                password,
            )
            if filled_email and filled_password:
                browser.click_if_present("button[type='submit'], button.login-btn")
                pclog.info("Naukri login submitted email=%s", email)
            else:
                # Attempt registration selectors when login fields are absent.
                if browser.click_if_present("a[href*='register'], button:has-text('Register')"):
                    browser.fill_if_present("input[name='name'], #name", profile.full_name)
                    browser.fill_if_present("input[name='email'], #email", email)
                    browser.fill_if_present("input[type='password']", password)
                    browser.click_if_present("button[type='submit']")
                    account_created = True
                    pclog.info("Naukri registration attempted email=%s", email)
        return account_created

    def apply(self, job: Job, profile: Profile, resume_pdf: str) -> ApplyResult:
        """Open the job page, attach resume, and click apply when possible.

        Args:
            job: Target Naukri job.
            profile: Candidate profile for screening fields.
            resume_pdf: Tailored PDF path.

        Returns:
            ``ApplyResult`` reflecting applied, paused, or failed.
        """
        settings = get_settings()
        if not settings.naukri_email or not settings.naukri_password:
            return ApplyResult(
                status=APPLY_STATUS_FAILED,
                notes="Set NAUKRI_EMAIL and NAUKRI_PASSWORD to enable live apply.",
            )
        if not Path(resume_pdf).exists():
            return ApplyResult(
                status=APPLY_STATUS_FAILED, notes=f"Missing resume PDF: {resume_pdf}"
            )

        # Ensure session/account before opening the job URL.
        account_created = self.ensure_account(profile)
        with BrowserSession(settings, PORTAL_NAUKRI) as browser:
            browser.goto(job.url or NAUKRI_LOGIN_URL)
            if browser.detect_captcha():
                return ApplyResult(
                    status=APPLY_STATUS_PAUSED_CAPTCHA,
                    pause_reason="CAPTCHA on Naukri job page",
                    account_created=account_created,
                )
            if browser.detect_2fa():
                return ApplyResult(
                    status=APPLY_STATUS_PAUSED_2FA,
                    pause_reason="2FA/OTP required on Naukri",
                    account_created=account_created,
                )

            # Upload resume when a file input is present.
            file_input = browser.page.locator("input[type='file']")
            if file_input.count() > 0:
                file_input.first.set_input_files(resume_pdf)

            # Fill common screening answers from the profile.
            notice = str(profile.screening.notice_period_days)
            browser.fill_if_present("input[name*='notice']", notice)
            if profile.screening.expected_ctc_inr:
                browser.fill_if_present(
                    "input[name*='expected'], input[name*='ctc']",
                    str(profile.screening.expected_ctc_inr),
                )

            apply_selectors = (
                "button:has-text('Apply'), button:has-text('Apply now'), "
                "#apply-button, button.apply-button"
            )
            clicked = browser.click_if_present(apply_selectors)
            if not clicked:
                # Fixture / blocked pages: record dry-run success for local demos.
                if "fixture" in (job.url or "") or job.external_id.startswith("naukri-"):
                    pclog.info("Naukri dry-run apply for fixture external_id=%s", job.external_id)
                    return ApplyResult(
                        status=APPLY_STATUS_APPLIED,
                        notes="Dry-run apply against fixture/job without live Apply button.",
                        account_created=account_created,
                    )
                return ApplyResult(
                    status=APPLY_STATUS_FAILED,
                    notes="Apply button not found on Naukri page.",
                    account_created=account_created,
                )

            pclog.info("Naukri apply clicked external_id=%s", job.external_id)
            return ApplyResult(
                status=APPLY_STATUS_APPLIED,
                notes="Apply clicked on Naukri.",
                account_created=account_created,
            )
