"""Parse unified diffs and classify findings as changed/unchanged/unknown.

This module only reports whether a finding falls inside the added lines of a
diff. It deliberately does not distinguish "new" from "existing" findings: that
requires a baseline and ground-truth data, which is a later step.
"""

from __future__ import annotations

import re

_FILE_HEADER = re.compile(r"^\+\+\+ b/(.+)$")
_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def parse_unified_diff(text: str) -> dict[str, tuple[tuple[int, int], ...]]:
    """Map each file path to its sorted, merged added-line ranges.

    Ranges are 1-based and inclusive. Only added lines are tracked; removed and
    context lines advance the new-file line counter without producing ranges.
    Deleted files (``+++ /dev/null``) and rename/binary hunks are ignored, so
    their paths are simply absent from the result.
    """
    changed: dict[str, list[tuple[int, int]]] = {}
    current_file: str | None = None
    new_line = 0

    for raw in text.splitlines():
        if raw.startswith("+++ "):
            match = _FILE_HEADER.match(raw)
            current_file = match.group(1) if match else None
            new_line = 0
            continue
        if raw.startswith("---"):
            continue
        if raw.startswith("@@"):
            match = _HUNK_HEADER.match(raw)
            new_line = int(match.group(1)) if match else 0
            continue
        if current_file is None:
            continue
        if raw.startswith("+"):
            changed.setdefault(current_file, []).append((new_line, new_line))
            new_line += 1
        elif raw.startswith("-"):
            continue
        else:
            new_line += 1

    return {
        path: tuple(_merge(sorted(ranges)))
        for path, ranges in changed.items()
    }


def _merge(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in ranges:
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def classify_finding(
    path: str,
    start_line: int,
    end_line: int,
    changed_ranges: dict[str, tuple[tuple[int, int], ...]],
) -> str:
    """Classify a finding as changed/unchanged/unknown against a diff.

    ``unknown`` means the path is absent from the diff; ``changed`` means the
    finding's ``[start_line, end_line]`` overlaps an added range; ``unchanged``
    means the path changed but this finding is outside those ranges.
    """
    ranges = changed_ranges.get(path)
    if ranges is None:
        return "unknown"
    for range_start, range_end in ranges:
        if start_line <= range_end and end_line >= range_start:
            return "changed"
    return "unchanged"
