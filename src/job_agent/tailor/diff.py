"""Text diff helpers for tailored resume review."""

from __future__ import annotations

import difflib

from job_agent.logging_setup import get_logger

pclog = get_logger(__name__)


def build_text_diff(original: str, tailored: str, from_name: str, to_name: str) -> str:
    """Build a unified diff between original and tailored resume text.

    Args:
        original: Source resume text.
        tailored: Tailored resume text.
        from_name: Label for the original side.
        to_name: Label for the tailored side.

    Returns:
        Unified diff string (may be empty when identical).
    """
    diff_lines = list(
        difflib.unified_diff(
            original.splitlines(),
            tailored.splitlines(),
            fromfile=from_name,
            tofile=to_name,
            lineterm="",
        )
    )
    diff_text = "\n".join(diff_lines)
    pclog.debug("Built diff lines=%s chars=%s", len(diff_lines), len(diff_text))
    return diff_text
