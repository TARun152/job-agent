"""Apply adapter registry."""

from __future__ import annotations

from job_agent.apply.instahyre import InstahyreApplyAdapter
from job_agent.apply.linkedin import LinkedInApplyAdapter
from job_agent.apply.naukri import NaukriApplyAdapter
from job_agent.apply.types import ApplyAdapter
from job_agent.apply.workday import WorkdayApplyAdapter
from job_agent.constants.portals import (
    PORTAL_INSTAHYRE,
    PORTAL_LINKEDIN,
    PORTAL_NAUKRI,
    PORTAL_WORKDAY,
)
from job_agent.logging_setup import get_logger

pclog = get_logger(__name__)


def get_apply_adapter(portal: str) -> ApplyAdapter:
    """Return the apply adapter for a portal id.

    Args:
        portal: Portal identifier.

    Returns:
        Concrete ``ApplyAdapter``.

    Raises:
        ValueError: If the portal is unknown.
    """
    adapters: dict[str, ApplyAdapter] = {
        PORTAL_NAUKRI: NaukriApplyAdapter(),
        PORTAL_INSTAHYRE: InstahyreApplyAdapter(),
        PORTAL_LINKEDIN: LinkedInApplyAdapter(),
        PORTAL_WORKDAY: WorkdayApplyAdapter(),
    }
    adapter = adapters.get(portal)
    if adapter is None:
        pclog.error("No apply adapter for portal=%s", portal)
        raise ValueError(f"Unsupported portal: {portal}")
    return adapter
