"""Common job posting model and SQLAlchemy persistence row."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from job_agent.constants.statuses import JOB_STATUS_DISCOVERED
from job_agent.db.base import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class Job(BaseModel):
    """Normalized job posting shared by every portal adapter."""

    external_id: str
    portal: str
    title: str
    company: str
    location: str = ""
    description: str = ""
    url: str = ""
    salary_text: str = ""
    posted_at: str = ""
    raw_keywords: list[str] = Field(default_factory=list)
    is_remote: bool = False

    def keyword_set(self) -> set[str]:
        """Return lowercase keywords from title, skills list, and description tokens.

        Returns:
            Set of normalized keyword strings.
        """
        tokens = {kw.strip().lower() for kw in self.raw_keywords if kw.strip()}
        for part in self.title.replace("/", " ").split():
            cleaned = part.strip(".,()[]").lower()
            if cleaned:
                tokens.add(cleaned)
        return tokens


class JobRecord(Base):
    """Persisted discovered job and match metadata."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    portal: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512))
    company: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(1024), default="")
    salary_text: Mapped[str] = mapped_column(String(255), default="")
    posted_at: Mapped[str] = mapped_column(String(64), default="")
    is_remote: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(64), default=JOB_STATUS_DISCOVERED)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_rationale: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    def to_job(self) -> Job:
        """Convert the ORM row into the shared pydantic Job model.

        Returns:
            ``Job`` domain object.
        """
        return Job(
            external_id=self.external_id,
            portal=self.portal,
            title=self.title,
            company=self.company,
            location=self.location,
            description=self.description,
            url=self.url,
            salary_text=self.salary_text,
            posted_at=self.posted_at,
            is_remote=self.is_remote,
        )
