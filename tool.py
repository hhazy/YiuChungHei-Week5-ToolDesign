"""
Core text/date tools (no API calls). Tool class + 3 tools.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable, Sequence

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


class Tool:
    def __init__(self, name: str, description: str, fn: Callable[..., Any]):
        self.name = name
        self.description = description
        self.fn = fn

    def execute(self, **kwargs: Any) -> Any:
        return self.fn(**kwargs)


def count_sentence(text: str) -> int:
    """
    Count the number of sentences in `text`.

    Rule:
    - Count sentence-ending punctuation: '.', '!' or '?' when followed by whitespace
      or end-of-string.

    Args:
        text: Input text.

    Returns:
        Number of sentences.

    Raises:
        ValueError: If `text` is not a non-empty string.
    """

    if not isinstance(text, str):
        raise ValueError("text must be a string")
    stripped = text.strip()
    if not stripped:
        raise ValueError("text is empty")
    return int(len(re.findall(r"[.!?]+(?:\s|$)", stripped)))


def count_words(text: str) -> int:
    """
    Count the number of words in `text`.

    Rule:
    - A word is a sequence of letters/numbers/apostrophes separated by whitespace
      or punctuation.

    Args:
        text: Input text.

    Returns:
        Number of words.

    Raises:
        ValueError: If `text` is not a non-empty string.
    """

    if not isinstance(text, str):
        raise ValueError("text must be a string")
    stripped = text.strip()
    if not stripped:
        raise ValueError("text is empty")
    return int(len(re.findall(r"[A-Za-z0-9']+", stripped)))


def parse_date(date_time_str: str) -> str:
    """
    Convert an input datetime string to HKT (Hong Kong Time) in ISO 8601 format.

    Input requirements:
    - The input must include timezone information (offset like +09:00, -04:00, or 'Z').

    Output:
    - ISO 8601 datetime string in HKT, with seconds and timezone offset, e.g.:
      "2026-02-27T18:30:00+08:00"

    Args:
        date_time_str: A datetime string with timezone info.

    Returns:
        ISO 8601 datetime string in HKT (UTC+08:00).

    Raises:
        ValueError: If the datetime cannot be parsed or has no timezone.
    """

    raw = (date_time_str or "").strip()
    if not raw:
        raise ValueError("Empty datetime string")
    if ZoneInfo is None:
        raise ValueError("zoneinfo is not available; cannot convert to HKT")

    dt = _parse_datetime_with_tz(raw)
    hkt = ZoneInfo("Asia/Hong_Kong")
    return dt.astimezone(hkt).isoformat(timespec="seconds")


def _parse_datetime_with_tz(value: str) -> datetime:
    """
    Best-effort parser for datetimes that include timezone info.
    Keeps parsing simple and beginner-friendly.
    """

    v = value.strip()

    # Handle common ISO "Z"
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"

    # 1) Try ISO 8601 via fromisoformat (supports offsets like +08:00)
    try:
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            raise ValueError("Datetime string missing timezone info")
        return dt
    except Exception:
        pass

    # 2) Try a small set of common patterns
    patterns: Sequence[str] = (
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M%z",
        "%Y/%m/%d %H:%M:%S%z",
        "%Y/%m/%d %H:%M%z",
        "%d %b %Y %H:%M:%S%z",
        "%d %b %Y %H:%M%z",
        "%b %d, %Y %H:%M:%S%z",
        "%b %d, %Y %H:%M%z",
    )
    for fmt in patterns:
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unrecognised datetime format or missing timezone: {value}")


TOOL_COUNT_SENTENCE = Tool(
    "count_sentence",
    "Count the number of sentences in text ( . ! ? followed by space or end).",
    count_sentence,
)
TOOL_COUNT_WORDS = Tool(
    "count_words",
    "Count the number of words in text (letters/numbers/apostrophes).",
    count_words,
)
TOOL_PARSE_DATE = Tool(
    "parse_date",
    "Parse datetime string with timezone and convert to HKT ISO 8601.",
    parse_date,
)