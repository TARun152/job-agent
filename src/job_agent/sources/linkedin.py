"""LinkedIn job discovery adapter."""

from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import urlencode

from job_agent.constants.portals import LINKEDIN_JOBS_SEARCH_URL, PORTAL_LINKEDIN
from job_agent.logging_setup import get_logger
from job_agent.models.job import Job
from job_agent.sources.base import JobSource
from job_agent.sources.browser_fetch import fetch_html_optional
from job_agent.sources.fixtures import fixture_jobs_for_portal
from job_agent.sources.html_parse import parse_generic_job_cards

pclog = get_logger(__name__)


class LinkedInSource(JobSource):
    """Discover public LinkedIn job cards; fixtures when auth wall blocks."""

    portal = PORTAL_LINKEDIN

    def search(self, keywords: Sequence[str], locations: Sequence[str], limit: int) -> list[Job]:
        """Search LinkedIn jobs (public HTML when available).

        LinkedIn frequently requires login. Documented login:
        set ``LINKEDIN_EMAIL`` / ``LINKEDIN_PASSWORD`` and use the apply
        browser session for authenticated discovery in a later hardening pass.

        Args:
            keywords: Role/skill keywords.
            locations: Preferred locations.
            limit: Max jobs.

        Returns:
            Normalized ``Job`` list.
        """
        params = {
            "keywords": " ".join(keywords[:5]),
            "location": locations[0] if locations else "India",
        }
        url = f"{LINKEDIN_JOBS_SEARCH_URL}?{urlencode(params)}"
        pclog.info("LinkedIn search url=%s limit=%s", url, limit)

        html = fetch_html_optional(url)
        if html:
            try:
                parsed = parse_generic_job_cards(
                    html=html,
                    portal=PORTAL_LINKEDIN,
                    card_selector=(
                        "div.base-card, li.jobs-search-results__list-item, div.job-search-card"
                    ),
                    title_selector="h3, a.base-card__full-link, a",
                    company_selector="h4, a.hidden-nested-link, span",
                    location_selector=(
                        ".job-search-card__location, span.job-search-card__location"
                    ),
                    limit=limit,
                )
            except Exception:
                pclog.warning("LinkedIn HTML parse failed; using fixtures", exc_info=True)
                parsed = []
            if parsed:
                pclog.info("LinkedIn live parse jobs=%s", len(parsed))
                return parsed
            pclog.warning("LinkedIn HTML present but selectors matched zero cards")

        fixtures = fixture_jobs_for_portal(PORTAL_LINKEDIN, limit)
        pclog.warning("LinkedIn using fixture jobs count=%s", len(fixtures))
        return fixtures
