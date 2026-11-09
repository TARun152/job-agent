"""Optional HTTP HTML fetch for discovery adapters."""

from __future__ import annotations

import httpx

from job_agent.constants.http_const import DEFAULT_USER_AGENT, HTML_FETCH_TIMEOUT_SEC
from job_agent.logging_setup import get_logger

pclog = get_logger(__name__)


def fetch_html_optional(url: str) -> str | None:
    """Fetch page HTML; return ``None`` on any network or HTTP failure.

    Args:
        url: Absolute URL to GET.

    Returns:
        Response text, or ``None`` if the request fails or is blocked.
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    try:
        response = httpx.get(
            url, headers=headers, follow_redirects=True, timeout=HTML_FETCH_TIMEOUT_SEC
        )
        if response.status_code >= 400:
            pclog.warning("HTML fetch status=%s url=%s", response.status_code, url)
            return None
        pclog.debug("HTML fetch ok chars=%s url=%s", len(response.text), url)
        return response.text
    except httpx.HTTPError:
        pclog.warning("HTML fetch failed url=%s", url, exc_info=True)
        return None
