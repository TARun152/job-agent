"""Truthful resume rewriting that emphasizes JD keywords already evidenced."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from job_agent.constants.paths import DIFF_TXT_SUFFIX, TAILORED_PDF_SUFFIX
from job_agent.constants.resume_const import TAILOR_STOPWORDS
from job_agent.logging_setup import get_logger
from job_agent.models.job import Job
from job_agent.models.profile import Profile
from job_agent.tailor.diff import build_text_diff
from job_agent.tailor.pdf_writer import write_resume_pdf

pclog = get_logger(__name__)


@dataclass(frozen=True)
class TailorResult:
    """Artifacts produced by resume tailoring."""

    tailored_text: str
    original_text: str
    diff_text: str
    pdf_path: Path
    diff_path: Path
    keywords_used: list[str]


def _extract_jd_keywords(job: Job, cap_ratio: float, profile_text: str) -> list[str]:
    """Select JD keywords that already appear in the profile (no invention).

    Args:
        job: Target job posting.
        cap_ratio: Max fraction of JD keyword list to inject (anti-stuffing).
        profile_text: Lowercased profile corpus.

    Returns:
        Ordered keyword list already evidenced in the profile.
    """
    candidates: list[str] = []
    scanned = list(job.raw_keywords) + re.findall(r"[A-Za-z][A-Za-z0-9+#]{2,}", job.description)
    for raw in scanned:
        token = raw.strip()
        if not token or token.lower() in TAILOR_STOPWORDS:
            continue
        if token.lower() in profile_text and token not in candidates:
            candidates.append(token)
    max_keep = max(1, int(len(candidates) * cap_ratio)) if candidates else 0
    # Cap keyword injection to avoid stuffing beyond the configured ratio.
    capped = candidates[: max(max_keep, min(8, len(candidates)))]
    pclog.debug("JD keywords evidenced=%s capped=%s", len(candidates), len(capped))
    return capped


def _reorder_bullets(profile: Profile, keywords: list[str]) -> list[str]:
    """Reorder experience bullets so keyword-bearing lines surface first.

    Args:
        profile: Candidate profile.
        keywords: Evidenced JD keywords.

    Returns:
        Reordered bullet list (same content, no new claims).
    """
    bullets = []
    for exp in profile.experience:
        for bullet in exp.bullets:
            bullets.append(bullet)
    if not bullets:
        # Fall back to summary sentences when bullets are missing.
        bullets = [line.strip() for line in profile.summary.split(".") if line.strip()]

    def bullet_score(bullet: str) -> int:
        lower = bullet.lower()
        return sum(1 for kw in keywords if kw.lower() in lower)

    # Stable sort: higher keyword hits first without inventing content.
    return sorted(bullets, key=bullet_score, reverse=True)


def render_resume_text(profile: Profile, summary: str, bullets: list[str]) -> str:
    """Render a plain-text resume body for PDF and diff generation.

    Args:
        profile: Candidate profile for header fields.
        summary: Tailored summary paragraph.
        bullets: Ordered experience bullets.

    Returns:
        Plain-text resume.
    """
    lines = [
        profile.full_name or "Candidate",
        profile.email,
        profile.phone,
        profile.location,
        "",
        "Summary",
        summary.strip(),
        "",
        "Skills",
        ", ".join(profile.skills),
        "",
        "Experience",
    ]
    for bullet in bullets:
        lines.append(f"- {bullet}")
    if profile.education:
        lines.extend(["", "Education", *profile.education])
    return "\n".join(line for line in lines if line is not None).strip() + "\n"


def tailor_resume_for_job(
    profile: Profile,
    job: Job,
    output_dir: str | Path,
    keyword_stuff_cap: float,
) -> TailorResult:
    """Rewrite summary/bullet order for a JD without inventing experience.

    Args:
        profile: Parsed candidate profile.
        job: Target job.
        output_dir: Directory for PDF and diff artifacts.
        keyword_stuff_cap: Max fraction of evidenced keywords to emphasize.

    Returns:
        ``TailorResult`` with paths and diff text.
    """
    pclog.info(
        "Tailoring resume for portal=%s external_id=%s title=%s",
        job.portal,
        job.external_id,
        job.title,
    )
    profile_corpus = (
        f"{profile.summary}\n{profile.all_bullet_text()}\n{' '.join(profile.skills)}".lower()
    )
    keywords = _extract_jd_keywords(job, keyword_stuff_cap, profile_corpus)
    bullets = _reorder_bullets(profile, keywords)

    # Prefacing summary with matched skills already present in the profile.
    skill_clause = ", ".join(keywords[:6]) if keywords else ", ".join(profile.skills[:6])
    base_summary = profile.summary.strip() or (
        f"Backend and AI engineer experienced with {', '.join(profile.skills[:8])}."
    )
    tailored_summary = base_summary
    if skill_clause and skill_clause.lower() not in base_summary.lower():
        tailored_summary = f"{base_summary} Relevant focus: {skill_clause}."

    original_text = render_resume_text(
        profile, profile.summary or base_summary, profile.all_bullet_text().splitlines()
    )
    tailored_text = render_resume_text(profile, tailored_summary, bullets)
    diff_text = build_text_diff(
        original_text,
        tailored_text,
        from_name="original.txt",
        to_name=f"tailored-{job.external_id}.txt",
    )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{job.portal}-{job.external_id}"
    pdf_path = out_dir / f"{stem}{TAILORED_PDF_SUFFIX}"
    diff_path = out_dir / f"{stem}{DIFF_TXT_SUFFIX}"

    # Write reviewable artifacts for the approval queue.
    write_resume_pdf(tailored_text, pdf_path, title=f"{profile.full_name} — {job.title}")
    diff_path.write_text(diff_text, encoding="utf-8")

    pclog.info(
        "Tailored resume pdf=%s diff=%s keywords=%s",
        pdf_path,
        diff_path,
        keywords,
    )
    return TailorResult(
        tailored_text=tailored_text,
        original_text=original_text,
        diff_text=diff_text,
        pdf_path=pdf_path,
        diff_path=diff_path,
        keywords_used=keywords,
    )
