"""LinkedIn apply adapter (stubbed interface matching other portals)."""

from __future__ import annotations

from job_agent.apply.types import ApplyAdapter, ApplyResult
from job_agent.constants.apply import APPLY_STATUS_FAILED
from job_agent.constants.portals import PORTAL_LINKEDIN
from job_agent.logging_setup import get_logger
from job_agent.models.job import Job
from job_agent.models.profile import Profile

pclog = get_logger(__name__)


class LinkedInApplyAdapter(ApplyAdapter):
    """Stubbed LinkedIn Easy Apply — same interface as Naukri/Instahyre."""

    portal = PORTAL_LINKEDIN

    def ensure_account(self, profile: Profile) -> bool:
        """LinkedIn account creation is not automated (ToS / bot risk).

        Args:
            profile: Candidate profile (unused).

        Returns:
            Always ``False``.
        """
        del profile
        pclog.info("LinkedIn ensure_account stubbed; use an existing logged-in session")
        return False

    def apply(self, job: Job, profile: Profile, resume_pdf: str) -> ApplyResult:
        """Return a stub failure with manual next steps.

        Args:
            job: Target LinkedIn job.
            profile: Candidate profile.
            resume_pdf: Tailored PDF path for manual upload.

        Returns:
            Failed ``ApplyResult`` describing the stub.
        """
        del profile
        pclog.warning(
            "LinkedIn apply stubbed external_id=%s resume=%s", job.external_id, resume_pdf
        )
        return ApplyResult(
            status=APPLY_STATUS_FAILED,
            notes=(
                "LinkedIn Easy Apply is stubbed. Log in once via sessions/linkedin, "
                f"then apply manually at {job.url} with {resume_pdf}."
            ),
        )
