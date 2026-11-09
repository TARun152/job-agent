"""OTP extraction from verification emails."""

from __future__ import annotations

import re

from job_agent.constants.gmail_const import OTP_CONTEXT_PATTERN, OTP_PATTERN
from job_agent.logging_setup import get_logger

pclog = get_logger(__name__)


def extract_otp_from_text(text: str) -> str | None:
    """Extract a one-time code from email body text.

    Prefers codes near OTP/verification wording, then falls back to the first
    standalone 4–8 digit number.

    Args:
        text: Email plain text or snippet.

    Returns:
        OTP string, or ``None`` if not found.
    """
    if not text:
        return None
    contextual = re.search(OTP_CONTEXT_PATTERN, text, flags=re.IGNORECASE)
    if contextual:
        code = contextual.group(1)
        pclog.info("Extracted contextual OTP digits=%s", len(code))
        return code
    fallback = re.search(OTP_PATTERN, text)
    if fallback:
        code = fallback.group(1)
        pclog.info("Extracted fallback OTP digits=%s", len(code))
        return code
    pclog.warning("No OTP found in email text chars=%s", len(text))
    return None
