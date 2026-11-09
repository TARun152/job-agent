"""Workday apply adapter (stubbed interface matching other portals)."""

from __future__ import annotations

from job_agent.apply.types import ApplyAdapter, ApplyResult
from job_agent.constants.apply import APPLY_STATUS_FAILED
from job_agent.constants.portals import PORTAL_WORKDAY
from job_agent.logging_setup import get_logger
from job_agent.models.job import Job
from job_agent.models.profile import Profile

pclog = get_logger(__name__)


class WorkdayApplyAdapter(ApplyAdapter):
    """Stubbed Workday apply — interface-compatible placeholder."""

    portal = PORTAL_WORKDAY

    def ensure_account(self, profile: Profile) -> bool:
        """Workday account creation varies per tenant; not automated yet.

        Args:
            profile: Candidate profile (unused).

        Returns:
            Always ``False``.
        """
        del profile
        pclog.info("Workday ensure_account stubbed")
        return False

    def apply(self, job: Job, profile: Profile, resume_pdf: str) -> ApplyResult:
        """Return a stub failure with manual next steps.

        Args:
            job: Target Workday job.
            profile: Candidate profile.
            resume_pdf: Tailored PDF path for manual upload.

        Returns:
            Failed ``ApplyResult`` describing the stub.
        """
        del profile
        pclog.warning("Workday apply stubbed external_id=%s resume=%s", job.external_id, resume_pdf)
        return ApplyResult(
            status=APPLY_STATUS_FAILED,
            notes=(
                "Workday apply is stubbed per-tenant. Open the career site listing "
                f"at {job.url} and upload {resume_pdf} manually after approval."
            ),
        )
