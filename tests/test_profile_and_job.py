"""Unit tests for profile/job models and resume text parsing."""

from __future__ import annotations

from job_agent.models.job import Job
from job_agent.models.profile import Experience, Profile
from job_agent.resume.parser import build_profile_from_text

SAMPLE_RESUME = """
Ada Lovelace
ada@example.com
+91 98765 43210
https://github.com/example

Summary
Backend and AI engineer with Python, Java, RAG, and NLP experience.

Skills
Python, Java, FastAPI, RAG, LLM, NLP, Docker, SQL

Experience
AI Engineer at Example Labs
- Built RAG pipelines over enterprise docs using Python and FastAPI
- Integrated LLM providers and evaluated retrieval quality
- Shipped Java interop services for ranking

Education
B.Tech Computer Science
""".strip()


def test_build_profile_from_text_extracts_core_fields() -> None:
    profile = build_profile_from_text(SAMPLE_RESUME)
    assert profile.email == "ada@example.com"
    assert "Python" in profile.skills
    assert "RAG" in profile.skills
    assert profile.experience
    assert any("RAG" in bullet for bullet in profile.all_bullet_text().splitlines())


def test_profile_skill_set_is_lowercase() -> None:
    profile = Profile(skills=["Python", "RAG", "python"])
    assert profile.skill_set() == {"python", "rag"}


def test_job_keyword_set_includes_title_tokens() -> None:
    job = Job(
        external_id="1",
        portal="naukri",
        title="AI Backend Engineer",
        company="X",
        raw_keywords=["Python"],
    )
    keywords = job.keyword_set()
    assert "python" in keywords
    assert "backend" in keywords


def test_experience_model_defaults() -> None:
    exp = Experience(title="Engineer", company="Acme")
    assert exp.bullets == []
