"""Central logging configuration for the Job Agent."""

from __future__ import annotations

import logging
import sys

from job_agent.constants.logging_const import DEFAULT_LOG_FORMAT, DEFAULT_LOG_LEVEL


def get_logger(name: str) -> logging.Logger:
    """Return a module logger; ensure root handlers exist once.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        Configured ``logging.Logger`` instance.
    """
    root = logging.getLogger()
    if not root.handlers:
        # Attach a single stream handler so all modules share one format.
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        root.addHandler(handler)
        root.setLevel(DEFAULT_LOG_LEVEL)
    return logging.getLogger(name)


def configure_logging(level: str) -> None:
    """Set the root log level from settings.

    Args:
        level: Logging level name such as INFO or DEBUG.
    """
    root = logging.getLogger()
    if not root.handlers:
        get_logger(__name__)
    root.setLevel(level.upper())
