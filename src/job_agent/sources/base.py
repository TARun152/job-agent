"""Shared job-source interface and discovery orchestration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from job_agent.logging_setup import get_logger
from job_agent.models.job import Job

pclog = get_logger(__name__)


class JobSource(ABC):
    """Portal adapter that returns normalized ``Job`` objects."""

    portal: str

    @abstractmethod
    def search(self, keywords: Sequence[str], locations: Sequence[str], limit: int) -> list[Job]:
        """Search the portal for matching jobs.

        Args:
            keywords: Role and skill keywords.
            locations: Preferred locations (e.g. India, Remote).
            limit: Max jobs to return from this portal.

        Returns:
            List of normalized ``Job`` models.
        """


def discover_all(
    sources: Sequence[JobSource],
    keywords: Sequence[str],
    locations: Sequence[str],
    limit_per_source: int,
) -> list[Job]:
    """Run every adapter and flatten results.

    Args:
        sources: Portal adapters to query.
        keywords: Search keywords.
        locations: Location filters.
        limit_per_source: Cap per adapter.

    Returns:
        Combined job list (may include duplicates across portals).
    """
    pclog.info(
        "Discovering jobs sources=%s keywords=%s limit_per_source=%s",
        [source.portal for source in sources],
        list(keywords),
        limit_per_source,
    )
    jobs: list[Job] = []
    for source in sources:
        try:
            # Query one portal; continue on failure so others still run.
            found = source.search(keywords, locations, limit_per_source)
            pclog.info("Portal=%s discovered=%s", source.portal, len(found))
            jobs.extend(found)
        except Exception:
            pclog.error("Discovery failed portal=%s", source.portal, exc_info=True)
    pclog.info("Discovery complete total_jobs=%s", len(jobs))
    return jobs
