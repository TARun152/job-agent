"""Parse PDF/DOCX resumes into a structured ``Profile``."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from job_agent.constants.paths import RESUME_DOCX_SUFFIX, RESUME_PDF_SUFFIX
from job_agent.constants.resume_const import (
    EMAIL_PATTERN,
    KNOWN_SKILL_TOKENS,
    PHONE_PATTERN,
    SECTION_HEADERS,
    URL_PATTERN,
)
from job_agent.logging_setup import get_logger
from job_agent.models.profile import Experience, Profile, ScreeningAnswers

pclog = get_logger(__name__)


def extract_text_from_pdf(path: Path) -> str:
    """Extract plain text from a PDF resume.

    Args:
        path: Path to a ``.pdf`` file.

    Returns:
        Concatenated page text, or empty string on failure.
    """
    pclog.info("Extracting text from PDF path=%s", path)
    try:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            # Pull text from each page; missing extractors yield empty.
            pages.append(page.extract_text() or "")
        text = "\n".join(pages).strip()
        pclog.info("PDF extract chars=%s pages=%s path=%s", len(text), len(reader.pages), path)
        return text
    except Exception:
        pclog.error("Failed PDF extract path=%s", path, exc_info=True)
        return ""


def extract_text_from_docx(path: Path) -> str:
    """Extract plain text from a DOCX resume.

    Args:
        path: Path to a ``.docx`` file.

    Returns:
        Paragraph-joined text, or empty string on failure.
    """
    pclog.info("Extracting text from DOCX path=%s", path)
    try:
        document = Document(str(path))
        # Join non-empty paragraphs to preserve reading order.
        paragraphs = [para.text.strip() for para in document.paragraphs if para.text.strip()]
        text = "\n".join(paragraphs)
        pclog.info("DOCX extract chars=%s paragraphs=%s path=%s", len(text), len(paragraphs), path)
        return text
    except Exception:
        pclog.error("Failed DOCX extract path=%s", path, exc_info=True)
        return ""


def extract_resume_text(path: Path) -> str:
    """Dispatch to PDF or DOCX extraction by file suffix.

    Args:
        path: Resume file path.

    Returns:
        Extracted plain text.

    Raises:
        ValueError: If the suffix is unsupported.
    """
    suffix = path.suffix.lower()
    if suffix == RESUME_PDF_SUFFIX:
        return extract_text_from_pdf(path)
    if suffix == RESUME_DOCX_SUFFIX:
        return extract_text_from_docx(path)
    raise ValueError(f"Unsupported resume type: {suffix}")


def _first_match(pattern: str, text: str) -> str:
    """Return the first regex group or full match, else empty."""
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return ""
    return match.group(0)


def _detect_skills(text: str) -> list[str]:
    """Find known skill tokens mentioned in the resume body.

    Args:
        text: Full resume text.

    Returns:
        Deduped skill labels in discovery order.
    """
    lower = text.lower()
    found: list[str] = []
    for skill in KNOWN_SKILL_TOKENS:
        # Match whole-ish tokens to avoid tiny false positives.
        if re.search(rf"(?<![a-z0-9]){re.escape(skill.lower())}(?![a-z0-9])", lower):
            found.append(skill)
    return found


def _split_sections(text: str) -> dict[str, str]:
    """Split resume text into coarse named sections by common headers.

    Args:
        text: Full resume text.

    Returns:
        Mapping of section name to body text.
    """
    lines = [line.strip() for line in text.splitlines()]
    sections: dict[str, list[str]] = {
        "summary": [],
        "experience": [],
        "education": [],
        "skills": [],
    }
    current = "summary"
    for line in lines:
        header_key = None
        for name, aliases in SECTION_HEADERS.items():
            if line.lower().rstrip(":") in aliases:
                header_key = name
                break
        if header_key:
            current = header_key
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(vals).strip() for key, vals in sections.items()}


def _parse_experience_blocks(experience_text: str) -> list[Experience]:
    """Heuristic parse of experience lines into company/title/bullet entries.

    Args:
        experience_text: Experience section body.

    Returns:
        List of ``Experience`` objects (may be empty).
    """
    if not experience_text.strip():
        return []
    blocks: list[Experience] = []
    current: Experience | None = None
    for line in experience_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Treat lines with " - " or " @" as role headers.
        if " at " in stripped.lower() or " | " in stripped or " - " in stripped:
            if current:
                blocks.append(current)
            title = stripped
            company = ""
            for sep in (" at ", " @ ", " | ", " - "):
                if sep in stripped:
                    left, right = stripped.split(sep, 1)
                    title, company = left.strip(), right.strip()
                    break
            current = Experience(title=title, company=company, bullets=[])
            continue
        if current is None:
            current = Experience(title="Experience", bullets=[])
        bullet = stripped.lstrip("•-* ").strip()
        if bullet:
            current.bullets.append(bullet)
    if current:
        blocks.append(current)
    pclog.debug("Parsed experience blocks count=%s", len(blocks))
    return blocks


def build_profile_from_text(text: str, notice_period_days: int = 30) -> Profile:
    """Build a structured profile from raw resume text.

    Args:
        text: Plain-text resume body.
        notice_period_days: Default notice period for screening answers.

    Returns:
        Populated ``Profile`` (fields may be empty if text is sparse).
    """
    pclog.info("Building profile from text chars=%s", len(text))
    sections = _split_sections(text)
    email = _first_match(EMAIL_PATTERN, text)
    phone = _first_match(PHONE_PATTERN, text)
    links = re.findall(URL_PATTERN, text)
    skills = _detect_skills(text)
    if sections.get("skills"):
        # Merge explicit skills section tokens with known-token hits.
        for token in re.split(r"[,|/•\n]", sections["skills"]):
            cleaned = token.strip()
            if cleaned and cleaned not in skills:
                skills.append(cleaned)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    full_name = lines[0] if lines else ""
    experience = _parse_experience_blocks(sections.get("experience", ""))
    education = [
        line.strip() for line in sections.get("education", "").splitlines() if line.strip()
    ]
    profile = Profile(
        full_name=full_name,
        email=email,
        phone=phone,
        summary=sections.get("summary", "")[:2000],
        skills=skills,
        experience=experience,
        education=education,
        links=links,
        raw_text=text,
        screening=ScreeningAnswers(notice_period_days=notice_period_days),
    )
    pclog.info(
        "Profile built name=%s email_set=%s skills=%s experience=%s",
        profile.full_name,
        bool(profile.email),
        len(profile.skills),
        len(profile.experience),
    )
    return profile


def parse_resume_file(path: Path, notice_period_days: int = 30) -> Profile:
    """Parse a single resume file into a ``Profile``.

    Args:
        path: PDF or DOCX path.
        notice_period_days: Default notice period for screening.

    Returns:
        Parsed ``Profile``.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the file type is unsupported or empty.
    """
    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {path}")
    # Extract plain text then structure it.
    text = extract_resume_text(path)
    if not text.strip():
        raise ValueError(f"Resume text empty: {path}")
    return build_profile_from_text(text, notice_period_days=notice_period_days)


def load_profile_from_resume_dir(resume_dir: str | Path, notice_period_days: int = 30) -> Profile:
    """Load the first PDF/DOCX found in the resume upload directory.

    Args:
        resume_dir: Directory containing the uploaded resume.
        notice_period_days: Default notice period for screening.

    Returns:
        Parsed ``Profile``.

    Raises:
        FileNotFoundError: If no supported resume file is present.
    """
    directory = Path(resume_dir)
    pclog.info("Scanning resume dir=%s", directory)
    candidates = sorted(
        [
            path
            for path in directory.iterdir()
            if path.is_file()
            and path.suffix.lower() in {RESUME_PDF_SUFFIX, RESUME_DOCX_SUFFIX}
            and path.name != ".gitkeep"
        ]
    )
    if not candidates:
        raise FileNotFoundError(
            f"No PDF/DOCX resume found in {directory}. Place a file under resume/."
        )
    # Prefer the first file by name for deterministic local runs.
    chosen = candidates[0]
    pclog.info("Using resume file=%s", chosen.name)
    return parse_resume_file(chosen, notice_period_days=notice_period_days)
