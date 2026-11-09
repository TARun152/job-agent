"""Lightweight HTML card parsing without a heavy DOM dependency."""

from __future__ import annotations

import hashlib
import re
from html import unescape

from job_agent.logging_setup import get_logger
from job_agent.models.job import Job

pclog = get_logger(__name__)


def _strip_tags(fragment: str) -> str:
    """Remove HTML tags and unescape entities."""
    no_tags = re.sub(r"<[^>]+>", " ", fragment)
    return unescape(re.sub(r"\s+", " ", no_tags)).strip()


def _first_attr(fragment: str, attr: str) -> str:
    """Extract the first HTML attribute value from a fragment."""
    match = re.search(rf'{attr}=["\']([^"\']+)["\']', fragment, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def parse_generic_job_cards(
    html: str,
    portal: str,
    card_selector: str,
    title_selector: str,
    company_selector: str,
    location_selector: str,
    limit: int,
) -> list[Job]:
    """Parse job cards using coarse CSS-class heuristics via regex.

    This is intentionally tolerant rather than perfect: portal markup changes
    often, and fixtures cover offline runs. Selectors are comma-separated class
    or tag hints; the first matching strategy that yields cards is used.

    Args:
        html: Raw HTML document.
        portal: Portal id for the Job model.
        card_selector: Comma-separated card hints (class/tag).
        title_selector: Unused beyond logging; title taken from anchors/headings.
        company_selector: Unused beyond logging.
        location_selector: Unused beyond logging.
        limit: Max jobs.

    Returns:
        Parsed ``Job`` list (possibly empty).
    """
    del title_selector, company_selector, location_selector  # kept for adapter clarity
    jobs: list[Job] = []
    # Prefer article/div blocks that look like job cards by class substrings.
    class_hints = []
    for part in card_selector.split(","):
        part = part.strip()
        if "." in part:
            class_hints.append(part.split(".", 1)[1].split(".", 1)[0])
    # Non-capturing groups for class hints so findall returns only tag + body.
    hints = "|".join(re.escape(hint) for hint in class_hints)
    pattern = re.compile(
        rf"<(article|div)\b[^>]*\bclass=(?:\"[^\"]*(?:{hints})[^\"]*\"|'[^']*(?:{hints})[^']*')[^>]*>(.*?)</\1>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    matches = pattern.findall(html) if class_hints else []
    pclog.debug("HTML card regex matches=%s portal=%s", len(matches), portal)

    for match in matches:
        if not isinstance(match, tuple) or len(match) < 2:
            continue
        _tag, body = match[0], match[1]
        if len(jobs) >= limit:
            break
        text = _strip_tags(body)
        if len(text) < 10:
            continue
        href = _first_attr(body, "href")
        # First non-trivial line as title; second as company when present.
        lines = [line.strip() for line in text.split("  ") if line.strip()]
        title = lines[0][:200] if lines else "Untitled"
        company = lines[1][:200] if len(lines) > 1 else "Unknown"
        location = ""
        for line in lines:
            lower = line.lower()
            if any(
                token in lower
                for token in ("india", "remote", "bengaluru", "bangalore", "hyderabad", "pune")
            ):
                location = line[:200]
                break
        external_id = hashlib.sha1(f"{portal}:{title}:{company}:{href}".encode()).hexdigest()[:16]
        jobs.append(
            Job(
                external_id=external_id,
                portal=portal,
                title=title,
                company=company,
                location=location,
                description=text[:4000],
                url=href,
                is_remote="remote" in text.lower(),
            )
        )
    pclog.info("Parsed generic cards portal=%s jobs=%s", portal, len(jobs))
    return jobs
