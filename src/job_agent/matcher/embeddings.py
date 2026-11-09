"""Optional OpenAI embeddings helper for semantic match boost."""

from __future__ import annotations

import math

from job_agent.logging_setup import get_logger

pclog = get_logger(__name__)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity between two equal-length vectors.

    Args:
        left: First embedding.
        right: Second embedding.

    Returns:
        Similarity in roughly ``[-1, 1]``, or ``0.0`` if a vector is empty.
    """
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def embed_texts_optional(
    texts: list[str],
    api_key: str,
    model: str,
) -> list[list[float]] | None:
    """Embed texts with OpenAI when a key is configured.

    Args:
        texts: Strings to embed.
        api_key: OpenAI API key (empty disables the call).
        model: Embedding model name.

    Returns:
        List of embedding vectors, or ``None`` if unavailable/failed.
    """
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        # Request embeddings for profile and job blobs in one batch.
        response = client.embeddings.create(model=model, input=texts)
        vectors = [list(item.embedding) for item in response.data]
        pclog.info("Embedded texts count=%s model=%s dims=%s", len(vectors), model, len(vectors[0]))
        return vectors
    except Exception:
        pclog.warning("Embedding call failed; continuing with heuristic score", exc_info=True)
        return None
