"""Backward-compatible re-exports for apply types."""

from job_agent.apply.registry import get_apply_adapter
from job_agent.apply.types import ApplyAdapter, ApplyResult

__all__ = ["ApplyAdapter", "ApplyResult", "get_apply_adapter"]
