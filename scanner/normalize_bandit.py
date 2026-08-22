"""Convert Bandit JSON into the normalized finding contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scanner.models import Finding, ScanDocument


_SEVERITIES = {"HIGH": "error", "MEDIUM": "warning", "LOW": "info"}


class BanditFormatError(ValueError):
    """Raised when Bandit JSON cannot be normalized safely."""


def _require_mapping(value: Any, pointer: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BanditFormatError(f"Expected an object at {pointer}")
    return value


def _require_value(payload: dict[str, Any], key: str, pointer: str) -> Any:
    if key not in payload:
        raise BanditFormatError(f"Missing required field at {pointer}/{key}")
    return payload[key]


def normalize_bandit(
    payload: dict[str, Any], tool_version: str, target: str
) -> ScanDocument:
    """Normalize Bandit's stable JSON fields without reading source files."""
    root = _require_mapping(payload, "/")
    results = _require_value(root, "results", "")
    _require_value(root, "errors", "")
    if not isinstance(results, list):
        raise BanditFormatError("Expected an array at /results")

    findings: list[Finding] = []
    for index, item in enumerate(results):
        pointer = f"/results/{index}"
        result = _require_mapping(item, pointer)
        raw_severity = _require_value(result, "issue_severity", pointer)
        metadata: dict[str, Any] = {"bandit_severity": raw_severity}
        more_info = result.get("more_info")
        if more_info:
            metadata["references"] = [more_info]
        line_number = _require_value(result, "line_number", pointer)
        line_range = result.get("line_range", [line_number])
        if not isinstance(line_range, list) or not line_range:
            raise BanditFormatError(f"Expected a non-empty array at {pointer}/line_range")
        findings.append(
            Finding.create(
                rule_id=_require_value(result, "test_id", pointer),
                severity=_SEVERITIES.get(raw_severity.upper(), "unknown"),
                path=Path(_require_value(result, "filename", pointer)).as_posix(),
                start_line=line_number,
                start_column=None,
                end_line=max(line_range),
                end_column=None,
                message=_require_value(result, "issue_text", pointer),
                code=result.get("code"),
                metadata=metadata,
                raw_reference=pointer,
                tool="bandit",
            )
        )

    return ScanDocument.create(
        tool_version, target, findings, tool="bandit", ruleset="bandit-default"
    )
