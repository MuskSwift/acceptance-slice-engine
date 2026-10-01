"""Exact H2 heading validation for the acceptance-slice contract."""

from __future__ import annotations

REQUIRED_HEADINGS: tuple[str, ...] = (
    "## 工单目标",
    "## 验收条目",
    "## 非本单 / 明确不做",
    "## 风险与 sev 提示",
    "## 给实现的边界",
    "## 待确认的开放问题",
)


def missing_headings(markdown: str) -> list[str]:
    """Return required H2 strings that are absent (exact substring match)."""
    return [heading for heading in REQUIRED_HEADINGS if heading not in markdown]


def validate_or_errors(markdown: str) -> list[str]:
    """Return errors for missing headings and for wrong heading order.

    An empty list means every required H2 is present and the first index of
    each heading is strictly ascending in ``REQUIRED_HEADINGS`` order.
    """
    errors: list[str] = []
    for heading in missing_headings(markdown):
        errors.append(f"missing heading: {heading}")

    found: list[tuple[int, str]] = []
    for heading in REQUIRED_HEADINGS:
        index = markdown.find(heading)
        if index != -1:
            found.append((index, heading))

    indexes = [index for index, _heading in found]
    if indexes != sorted(set(indexes)):
        expected = " → ".join(heading for _index, heading in found)
        observed = " → ".join(heading for _index, heading in sorted(found))
        errors.append(
            "wrong heading order: first occurrences are not strictly ascending; "
            f"expected {expected}; observed {observed}"
        )
    return errors
