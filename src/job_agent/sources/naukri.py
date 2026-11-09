"""Naukri job discovery adapter."""

from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import quote_plus

from job_agent.constants.portals import NAUKRI_BASE_URL, PORTAL_NAUKRI
from job_agent.logging_setup import get_logger
from job_agent.models.job import Job
from job_agent.sources.base import JobSource
from job_agent.sources.browser_fetch import fetch_html_optional
from job_agent.sources.fixtures import fixture_jobs_for_portal
from job_agent.sources.html_parse import parse_generic_job_cards

pclog = get_logger(__name__)


class NaukriSource(JobSource):
    """Discover jobs on Naukri via HTML parse with fixture fallback."""

    portal = PORTAL_NAUKRI

    def search(self, keywords: Sequence[str], locations: Sequence[str], limit: int) -> list[Job]:
        """Search Naukri for keyword matches.

        Live HTML parsing is best-effort; if selectors miss or the page is
        blocked, deterministic fixtures are returned so the pipeline still runs.

        Args:
            keywords: Role/skill keywords.
            locations: Preferred locations.
            limit: Max jobs.

        Returns:
            Normalized ``Job`` list.
        """
        query = "-".join(keywords[:3]).lower().replace(" ", "-")
        location = locations[0] if locations else "india"
        url = f"{NAUKRI_BASE_URL}/{quote_plus(query)}-jobs-in-{quote_plus(location.lower())}"
        pclog.info("Naukri search url=%s limit=%s", url, limit)

        # Attempt a light HTML fetch; many portals block datacenter IPs.
        html = fetch_html_optional(url)
        if html:
            parsed = parse_generic_job_cards(
                html=html,
                portal=PORTAL_NAUKRI,
                card_selector="article.jobTuple, div.srp-jobtuple-wrapper, div.jobTuple",
                title_selector="a.title, a[class*='title']",
                company_selector="a.subTitle, a[class*='company']",
                location_selector="span.locWdth, span[class*='loc']",
                limit=limit,
            )
            if parsed:
                pclog.info("Naukri live parse jobs=%s", len(parsed))
                return parsed
            pclog.warning("Naukri HTML present but selectors matched zero cards")

        # Fall back to fixtures so matcher/tailor/queue can be exercised offline.
        fixtures = fixture_jobs_for_portal(PORTAL_NAUKRI, limit)
        pclog.warning("Naukri using fixture jobs count=%s", len(fixtures))
        return fixtures
