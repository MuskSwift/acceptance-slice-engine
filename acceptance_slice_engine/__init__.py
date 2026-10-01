"""Acceptance Slice Engine v0 — Eng-dispatchable acceptance-slice Markdown."""

__version__ = "0.1.0"

from .validate import REQUIRED_HEADINGS, validate_or_errors

__all__ = ["REQUIRED_HEADINGS", "__version__", "validate_or_errors"]
