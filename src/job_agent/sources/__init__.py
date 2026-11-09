"""Job discovery portal adapters."""

from job_agent.sources.base import JobSource, discover_all
from job_agent.sources.instahyre import InstahyreSource
from job_agent.sources.linkedin import LinkedInSource
from job_agent.sources.naukri import NaukriSource
from job_agent.sources.workday import WorkdaySource

__all__ = [
    "InstahyreSource",
    "JobSource",
    "LinkedInSource",
    "NaukriSource",
    "WorkdaySource",
    "discover_all",
]
