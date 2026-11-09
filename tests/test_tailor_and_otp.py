"""Unit tests for tailoring diffs and Gmail OTP extraction."""

from __future__ import annotations

from pathlib import Path

from job_agent.gmail.otp import extract_otp_from_text
from job_agent.models.job import Job
from job_agent.models.profile import Experience, Profile
from job_agent.tailor.diff import build_text_diff
from job_agent.tailor.rewriter import tailor_resume_for_job


def test_extract_otp_contextual() -> None:
    assert extract_otp_from_text("Your verification code is 482193") == "482193"
    assert extract_otp_from_text("no codes here") is None


def test_build_text_diff_shows_change() -> None:
    diff = build_text_diff("hello\n", "hello\nworld\n", "a", "b")
    assert "+world" in diff


def test_tailor_resume_writes_artifacts(tmp_path: Path) -> None:
    profile = Profile(
        full_name="Ada Lovelace",
        email="ada@example.com",
        summary="Backend engineer using Python.",
        skills=["Python", "RAG", "LLM", "Java"],
        experience=[
            Experience(
                company="Example",
                title="AI Engineer",
                bullets=[
                    "Maintained billing APIs",
                    "Built RAG pipelines with Python and LLM evaluation",
                ],
            )
        ],
    )
    job = Job(
        external_id="t1",
        portal="naukri",
        title="RAG Engineer",
        company="DocuMind",
        description="Python RAG LLM retrieval",
        raw_keywords=["Python", "RAG", "LLM"],
    )
    result = tailor_resume_for_job(profile, job, tmp_path, keyword_stuff_cap=0.5)
    assert result.pdf_path.exists()
    assert result.diff_path.exists()
    assert "RAG" in result.tailored_text or "LLM" in result.tailored_text
