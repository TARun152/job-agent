"""Defaults for match scoring and keyword caps."""

# Heuristic-only scores typically land 0.45–0.75; embeddings raise this when configured.
DEFAULT_MATCH_THRESHOLD = 0.55
DEFAULT_KEYWORD_STUFF_CAP = 0.15

DEFAULT_ROLE_KEYWORDS = (
    "AI engineer",
    "backend engineer",
    "ML engineer",
    "NLP",
    "RAG",
    "LLM",
    "Python",
    "Java",
)

DEFAULT_LOCATIONS = ("India", "Remote")

# Heuristic weights when LLM is unavailable (offline / no API key).
WEIGHT_SKILL_OVERLAP = 0.45
WEIGHT_TITLE_OVERLAP = 0.25
WEIGHT_KEYWORD_OVERLAP = 0.20
WEIGHT_LOCATION_FIT = 0.10

MIN_SCORE = 0.0
MAX_SCORE = 1.0
