"""Unit tests for heuristic match scoring helpers."""

from __future__ import annotations

from job_agent.matcher.scorer import _clamp, _jaccard, _tokenize, score_job_against_profile
from job_agent.models.job import Job
from job_agent.models.profile import Profile


def test_tokenize_and_jaccard() -> None:
    tokens = _tokenize("Python RAG / LLM")
    assert "python" in tokens
    assert "rag" in tokens
    assert _jaccard({"a", "b"}, {"b", "c"}) == 1 / 3


def test_clamp_bounds() -> None:
    assert _clamp(-1) == 0.0
    assert _clamp(2) == 1.0
    assert _clamp(0.5) == 0.5


def test_score_job_against_profile_prefers_overlap() -> None:
    profile = Profile(
        summary="Python backend and RAG engineer",
        skills=["Python", "RAG", "LLM", "Java", "FastAPI"],
    )
    strong = Job(
        external_id="strong",
        portal="naukri",
        title="AI Backend Engineer",
        company="A",
        location="India Remote",
        description="Python FastAPI RAG LLM NLP services",
        raw_keywords=["Python", "RAG", "LLM", "NLP"],
        is_remote=True,
    )
    weak = Job(
        external_id="weak",
        portal="naukri",
        title="Sales Manager",
        company="B",
        location="New York",
        description="Quota, CRM, outbound calling",
        raw_keywords=["Salesforce", "Sales"],
        is_remote=False,
    )
    strong_score = score_job_against_profile(
        strong, profile, ["AI engineer", "backend", "RAG", "Python"], ["India"], True
    )
    weak_score = score_job_against_profile(
        weak, profile, ["AI engineer", "backend", "RAG", "Python"], ["India"], True
    )
    assert strong_score.score > weak_score.score
    assert strong_score.score >= 0.4
    assert "python" in [s.lower() for s in strong_score.skill_overlap]
