"""Heuristic and optional LLM-assisted job match scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass

from job_agent.constants.matching import (
    MAX_SCORE,
    MIN_SCORE,
    WEIGHT_KEYWORD_OVERLAP,
    WEIGHT_LOCATION_FIT,
    WEIGHT_SKILL_OVERLAP,
    WEIGHT_TITLE_OVERLAP,
)
from job_agent.logging_setup import get_logger
from job_agent.matcher.embeddings import cosine_similarity, embed_texts_optional
from job_agent.models.job import Job
from job_agent.models.profile import Profile

pclog = get_logger(__name__)


@dataclass(frozen=True)
class MatchResult:
    """Score and short rationale for a job/profile pair."""

    score: float
    rationale: str
    skill_overlap: list[str]
    missing_skills: list[str]


def _tokenize(text: str) -> set[str]:
    """Split text into lowercase alphanumeric tokens."""
    return {token for token in re.findall(r"[a-zA-Z][a-zA-Z0-9+#./-]{1,}", text.lower())}


def _clamp(score: float) -> float:
    """Clamp a score into ``[MIN_SCORE, MAX_SCORE]``."""
    return max(MIN_SCORE, min(MAX_SCORE, score))


def _jaccard(left: set[str], right: set[str]) -> float:
    """Jaccard similarity for two token sets."""
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def score_job_against_profile(
    job: Job,
    profile: Profile,
    role_keywords: list[str],
    locations: list[str],
    remote_ok: bool,
    openai_api_key: str = "",
    embedding_model: str = "text-embedding-3-small",
) -> MatchResult:
    """Score how well a job matches the candidate profile.

    Uses deterministic overlap features always. When an API key is present,
    blends in embedding cosine similarity between profile summary/skills and
    the job description.

    Args:
        job: Normalized job posting.
        profile: Parsed candidate profile.
        role_keywords: Target role keywords from settings.
        locations: Preferred locations.
        remote_ok: Whether remote roles are acceptable.
        openai_api_key: Optional API key for embeddings.
        embedding_model: Embedding model name.

    Returns:
        ``MatchResult`` with score in ``[0, 1]`` and rationale text.
    """
    pclog.info(
        "Scoring job portal=%s external_id=%s title=%s",
        job.portal,
        job.external_id,
        job.title,
    )
    profile_skills = profile.skill_set()
    job_tokens = job.keyword_set() | _tokenize(job.description) | _tokenize(job.title)
    skill_hits = sorted(skill for skill in profile_skills if skill in job_tokens)
    missing = sorted(token for token in job.raw_keywords if token.lower() not in profile_skills)[:8]

    # Prefer recall against JD skill asks so larger profiles are not punished.
    jd_skill_asks = {kw.lower() for kw in job.raw_keywords if kw.strip()} or job_tokens
    ask_hits = len([ask for ask in jd_skill_asks if ask in profile_skills])
    skill_recall = ask_hits / max(len(jd_skill_asks), 1)
    skill_precision = len(skill_hits) / max(len(profile_skills), 1)
    skill_score = 0.7 * skill_recall + 0.3 * skill_precision

    title_tokens = _tokenize(job.title)
    title_lower = job.title.lower()

    def _role_matches_title(role: str) -> bool:
        role_lower = role.lower()
        if role_lower in title_lower:
            return True
        # Allow "AI engineer" to match "AI Backend Engineer".
        role_tokens = _tokenize(role)
        return bool(role_tokens) and role_tokens.issubset(title_tokens)

    role_hits = sum(1 for role in role_keywords if _role_matches_title(role))
    title_score = max(
        min(1.0, role_hits / max(min(len(role_keywords), 3), 1)),
        _jaccard(title_tokens, _tokenize(" ".join(role_keywords))),
    )
    keyword_score = _jaccard({kw.lower() for kw in role_keywords}, job_tokens)

    location_score = 0.0
    job_location = job.location.lower()
    if job.is_remote and remote_ok:
        location_score = 1.0
    elif any(loc.lower() in job_location for loc in locations):
        location_score = 1.0
    elif not job_location:
        location_score = 0.5

    base = (
        WEIGHT_SKILL_OVERLAP * skill_score
        + WEIGHT_TITLE_OVERLAP * title_score
        + WEIGHT_KEYWORD_OVERLAP * keyword_score
        + WEIGHT_LOCATION_FIT * location_score
    )

    embedding_boost = 0.0
    if openai_api_key:
        # Blend semantic similarity when embeddings are available.
        profile_blob = f"{profile.summary}\n{' '.join(profile.skills)}"
        job_blob = f"{job.title}\n{job.description}"
        vectors = embed_texts_optional(
            [profile_blob, job_blob],
            api_key=openai_api_key,
            model=embedding_model,
        )
        if vectors is not None:
            embedding_boost = 0.25 * cosine_similarity(vectors[0], vectors[1])
            base = 0.75 * base + embedding_boost

    score = _clamp(base)
    rationale = (
        f"skills={len(skill_hits)}/{len(profile_skills)}; "
        f"title={title_score:.2f}; keywords={keyword_score:.2f}; "
        f"location={location_score:.2f}; embed_boost={embedding_boost:.2f}"
    )
    if skill_hits:
        rationale += f"; matched_skills={', '.join(skill_hits[:8])}"
    pclog.info(
        "Match score=%.3f portal=%s external_id=%s rationale=%s",
        score,
        job.portal,
        job.external_id,
        rationale,
    )
    return MatchResult(
        score=score,
        rationale=rationale,
        skill_overlap=skill_hits,
        missing_skills=missing,
    )
