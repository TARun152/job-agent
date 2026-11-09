"""Deterministic fixture jobs used when live portal HTML is unavailable."""

from __future__ import annotations

from job_agent.constants.portals import (
    PORTAL_INSTAHYRE,
    PORTAL_LINKEDIN,
    PORTAL_NAUKRI,
    PORTAL_WORKDAY,
)
from job_agent.models.job import Job

FIXTURE_JOBS: dict[str, list[Job]] = {
    PORTAL_NAUKRI: [
        Job(
            external_id="naukri-ai-backend-1",
            portal=PORTAL_NAUKRI,
            title="AI Backend Engineer",
            company="Nimbus Labs",
            location="Bengaluru, India",
            description=(
                "Build Python FastAPI services for RAG pipelines, LLM orchestration, "
                "and retrieval over enterprise documents. Strong NLP and Java interop a plus."
            ),
            url="https://www.naukri.com/job-listings-ai-backend-engineer-fixture",
            salary_text="25-40 LPA",
            raw_keywords=["Python", "FastAPI", "RAG", "LLM", "NLP", "Java"],
            is_remote=False,
        ),
        Job(
            external_id="naukri-ml-platform-2",
            portal=PORTAL_NAUKRI,
            title="ML Platform Engineer",
            company="Orbit AI",
            location="Hyderabad / Remote",
            description=(
                "Own ML platform APIs, feature stores, and backend services in Python. "
                "Experience with LLMs and RAG evaluation preferred."
            ),
            url="https://www.naukri.com/job-listings-ml-platform-engineer-fixture",
            raw_keywords=["Python", "ML", "LLM", "RAG", "backend"],
            is_remote=True,
        ),
    ],
    PORTAL_INSTAHYRE: [
        Job(
            external_id="instahyre-nlp-1",
            portal=PORTAL_INSTAHYRE,
            title="NLP Engineer",
            company="ContextWorks",
            location="Remote, India",
            description=(
                "Design NLP systems for classification and retrieval. "
                "Ship production Python services and evaluate LLM prompts."
            ),
            url="https://www.instahyre.com/job-fixture-nlp-engineer",
            raw_keywords=["NLP", "Python", "LLM", "RAG"],
            is_remote=True,
        ),
        Job(
            external_id="instahyre-backend-2",
            portal=PORTAL_INSTAHYRE,
            title="Senior Backend Engineer - AI Products",
            company="SignalStack",
            location="Pune, India",
            description=(
                "Backend ownership for AI product APIs. Python, Java, Kafka, "
                "and experience integrating LLM providers required."
            ),
            url="https://www.instahyre.com/job-fixture-backend-ai",
            raw_keywords=["Python", "Java", "backend", "LLM", "Kafka"],
            is_remote=False,
        ),
    ],
    PORTAL_LINKEDIN: [
        Job(
            external_id="linkedin-rag-1",
            portal=PORTAL_LINKEDIN,
            title="RAG Engineer",
            company="DocuMind",
            location="India (Remote)",
            description=(
                "Build retrieval-augmented generation systems: chunking, embeddings, "
                "vector search, and Python services exposing grounded answers."
            ),
            url="https://www.linkedin.com/jobs/view/fixture-rag-engineer",
            raw_keywords=["RAG", "Python", "embeddings", "LLM", "NLP"],
            is_remote=True,
        ),
    ],
    PORTAL_WORKDAY: [
        Job(
            external_id="workday-ai-svc-1",
            portal=PORTAL_WORKDAY,
            title="Software Engineer, AI Services",
            company="Northwind Systems",
            location="Bengaluru, India",
            description=(
                "Implement Java and Python microservices powering AI features. "
                "Familiarity with LLMs, NLP pipelines, and RAG preferred."
            ),
            url="https://northwind.wd5.myworkdayjobs.com/en-US/Careers/job/fixture-ai-services",
            raw_keywords=["Java", "Python", "LLM", "NLP", "RAG", "backend"],
            is_remote=False,
        ),
    ],
}


def fixture_jobs_for_portal(portal: str, limit: int) -> list[Job]:
    """Return up to ``limit`` fixture jobs for a portal.

    Args:
        portal: Portal identifier.
        limit: Max jobs to return.

    Returns:
        Fixture ``Job`` list (possibly empty).
    """
    jobs = FIXTURE_JOBS.get(portal, [])
    return jobs[:limit]
