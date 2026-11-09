"""Structured candidate profile parsed from a resume."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Experience(BaseModel):
    """One employment or project entry from the resume."""

    company: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = Field(default_factory=list)
    skills_used: list[str] = Field(default_factory=list)


class ScreeningAnswers(BaseModel):
    """Default answers for common portal screening questions."""

    notice_period_days: int = 30
    current_location: str = "India"
    willing_to_relocate: bool = True
    remote_ok: bool = True
    expected_ctc_inr: int | None = None
    current_ctc_inr: int | None = None
    total_experience_years: float | None = None
    work_authorization: str = "India"


class Profile(BaseModel):
    """Candidate profile used for matching, tailoring, and apply forms."""

    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    raw_text: str = ""
    screening: ScreeningAnswers = Field(default_factory=ScreeningAnswers)

    def skill_set(self) -> set[str]:
        """Return lowercase skill tokens for overlap scoring.

        Returns:
            Set of normalized skill strings.
        """
        return {skill.strip().lower() for skill in self.skills if skill.strip()}

    def all_bullet_text(self) -> str:
        """Flatten experience bullets into a single string for keyword scans.

        Returns:
            Newline-joined bullet text.
        """
        lines: list[str] = []
        for exp in self.experience:
            lines.extend(exp.bullets)
        return "\n".join(lines)
