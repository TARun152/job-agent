"""Resume tailoring, PDF output, and diffs."""

from job_agent.tailor.diff import build_text_diff
from job_agent.tailor.rewriter import TailorResult, tailor_resume_for_job

__all__ = ["TailorResult", "build_text_diff", "tailor_resume_for_job"]
