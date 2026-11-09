"""PDF generation for tailored resumes."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from job_agent.logging_setup import get_logger

pclog = get_logger(__name__)


def write_resume_pdf(text: str, path: Path, title: str) -> Path:
    """Write plain resume text to a simple multi-paragraph PDF.

    Args:
        text: Resume body.
        path: Destination PDF path.
        title: Document title metadata.

    Returns:
        The written ``path``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=LETTER, title=title)
    story = []
    for block in text.split("\n\n"):
        cleaned = block.replace("\n", "<br/>")
        # Escape minimal XML entities for reportlab Paragraph.
        cleaned = cleaned.replace("&", "&amp;").replace("<br/>", "[[BR]]")
        cleaned = cleaned.replace("<", "&lt;").replace(">", "&gt;")
        cleaned = cleaned.replace("[[BR]]", "<br/>")
        story.append(Paragraph(cleaned, styles["Normal"]))
        story.append(Spacer(1, 10))
    doc.build(story)
    pclog.info("Wrote tailored PDF path=%s chars=%s", path, len(text))
    return path
