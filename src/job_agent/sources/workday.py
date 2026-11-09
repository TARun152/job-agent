"""Workday career-site discovery adapter."""

from __future__ import annotations

import json
from collections.abc import Sequence

import httpx

from job_agent.constants.portals import PORTAL_WORKDAY, WORKDAY_JOBS_PATH
from job_agent.constants.workday_const import DEFAULT_WORKDAY_SITES
from job_agent.logging_setup import get_logger
from job_agent.models.job import Job
from job_agent.sources.base import JobSource
from job_agent.sources.fixtures import fixture_jobs_for_portal

pclog = get_logger(__name__)


class WorkdaySource(JobSource):
    """Query configured Workday CXS job search endpoints."""

    portal = PORTAL_WORKDAY

    def __init__(self, sites: Sequence[dict[str, str]] | None = None) -> None:
        """Store Workday tenant/site configs to query.

        Args:
            sites: Optional list of ``{tenant, site, host, company}`` dicts.
        """
        self.sites = list(sites) if sites is not None else list(DEFAULT_WORKDAY_SITES)

    def search(self, keywords: Sequence[str], locations: Sequence[str], limit: int) -> list[Job]:
        """Search configured Workday sites for keyword matches.

        Args:
            keywords: Role/skill keywords.
            locations: Preferred locations (soft filter).
            limit: Max jobs across all sites.

        Returns:
            Normalized ``Job`` list.
        """
        pclog.info(
            "Workday search sites=%s keywords=%s locations=%s limit=%s",
            len(self.sites),
            list(keywords),
            list(locations),
            limit,
        )
        jobs: list[Job] = []
        query_text = " ".join(keywords[:5])
        for site in self.sites:
            if len(jobs) >= limit:
                break
            remaining = limit - len(jobs)
            # Hit one tenant CXS endpoint for JSON postings.
            found = self._search_site(site, query_text, remaining)
            jobs.extend(found)

        if not jobs:
            fixtures = fixture_jobs_for_portal(PORTAL_WORKDAY, limit)
            pclog.warning("Workday using fixture jobs count=%s", len(fixtures))
            return fixtures
        return jobs[:limit]

    def _search_site(self, site: dict[str, str], query_text: str, limit: int) -> list[Job]:
        """POST the Workday CXS jobs API for one tenant/site.

        Args:
            site: Tenant configuration.
            query_text: Free-text search.
            limit: Max jobs for this site.

        Returns:
            Parsed jobs, or empty list on network/parse failure.
        """
        tenant = site["tenant"]
        site_id = site["site"]
        host = site["host"]
        path = WORKDAY_JOBS_PATH.format(tenant=tenant, site=site_id)
        url = f"https://{host}{path}"
        payload = {
            "appliedFacets": {},
            "limit": limit,
            "offset": 0,
            "searchText": query_text,
        }
        pclog.debug("Workday POST url=%s limit=%s", url, limit)
        try:
            response = httpx.post(url, json=payload, timeout=20.0)
            if response.status_code >= 400:
                pclog.warning(
                    "Workday HTTP status=%s tenant=%s",
                    response.status_code,
                    tenant,
                )
                return []
            data = response.json()
        except (httpx.HTTPError, json.JSONDecodeError):
            pclog.warning("Workday request failed tenant=%s", tenant, exc_info=True)
            return []

        postings = data.get("jobPostings") or []
        jobs: list[Job] = []
        for posting in postings[:limit]:
            title = posting.get("title") or "Untitled"
            external_path = posting.get("externalPath") or ""
            locations_text = posting.get("locationsText") or ""
            external_id = posting.get("bulletFields", [None])[0] or external_path or title
            jobs.append(
                Job(
                    external_id=f"workday-{tenant}-{external_id}",
                    portal=PORTAL_WORKDAY,
                    title=title,
                    company=site.get("company", tenant),
                    location=locations_text,
                    description=posting.get("jobPostingInfo", {}).get("jobDescription", "")
                    if isinstance(posting.get("jobPostingInfo"), dict)
                    else "",
                    url=f"https://{host}{external_path}" if external_path else url,
                    raw_keywords=list(query_text.split()),
                    is_remote="remote" in locations_text.lower(),
                )
            )
        pclog.info("Workday tenant=%s jobs=%s", tenant, len(jobs))
        return jobs
