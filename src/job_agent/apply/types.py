"""Shared apply result and adapter protocol types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from job_agent.models.job import Job
from job_agent.models.profile import Profile


@dataclass(frozen=True)
class ApplyResult:
    """Outcome of one apply attempt."""

    status: str
    notes: str = ""
    pause_reason: str = ""
    account_created: bool = False


class ApplyAdapter(ABC):
    """Portal-specific form filler and account bootstrap."""

    portal: str

    @abstractmethod
    def ensure_account(self, profile: Profile) -> bool:
        """Create an account when missing; return True if created."""

    @abstractmethod
    def apply(self, job: Job, profile: Profile, resume_pdf: str) -> ApplyResult:
        """Submit an application for an approved job."""
