"""Instahyre job discovery adapter."""

from __future__ import annotations

from collections.abc import Sequence

from job_agent.constants.portals import INSTAHYRE_SEARCH_URL, PORTAL_INSTAHYRE
from job_agent.logging_setup import get_logger
from job_agent.models.job import Job
from job_agent.sources.base import JobSource
from job_agent.sources.browser_fetch import fetch_html_optional
from job_agent.sources.fixtures import fixture_jobs_for_portal
from job_agent.sources.html_parse import parse_generic_job_cards

pclog = get_logger(__name__)


class InstahyreSource(JobSource):
    """Discover jobs on Instahyre with fixture fallback."""

    portal = PORTAL_INSTAHYRE

    def search(self, keywords: Sequence[str], locations: Sequence[str], limit: int) -> list[Job]:
        """Search Instahyre for matching roles.

        Args:
            keywords: Role/skill keywords.
            locations: Preferred locations (logged; filters applied client-side).
            limit: Max jobs.

        Returns:
            Normalized ``Job`` list.
        """
        query = " ".join(keywords[:4])
        url = f"{INSTAHYRE_SEARCH_URL}?q={query.replace(' ', '+')}"
        pclog.info(
            "Instahyre search url=%s locations=%s limit=%s",
            url,
            list(locations),
            limit,
        )

        html = fetch_html_optional(url)
        if html:
            parsed = parse_generic_job_cards(
                html=html,
                portal=PORTAL_INSTAHYRE,
                card_selector="div.opportunity, div.job-card, article",
                title_selector="a, h2, h3",
                company_selector=".company, .employer, span",
                location_selector=".location, .job-location",
                limit=limit,
            )
            if parsed:
                pclog.info("Instahyre live parse jobs=%s", len(parsed))
                return parsed
            pclog.warning("Instahyre HTML present but selectors matched zero cards")

        fixtures = fixture_jobs_for_portal(PORTAL_INSTAHYRE, limit)
        pclog.warning("Instahyre using fixture jobs count=%s", len(fixtures))
        return fixtures
