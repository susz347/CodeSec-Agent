"""Convert Semgrep CLI JSON into the normalized finding contract."""

from __future__ import annotations

from typing import Any

from scanner.models import Finding, ScanDocument


_METADATA_FIELDS = {"cwe", "owasp", "category", "technology", "references"}


class SemgrepFormatError(ValueError):
    """Raised when Semgrep JSON cannot be normalized safely."""


def _require_mapping(value: Any, pointer: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SemgrepFormatError(f"Expected an object at {pointer}")
    return value


def _require_value(payload: dict[str, Any], key: str, pointer: str) -> Any:
    if key not in payload:
        raise SemgrepFormatError(f"Missing required field at {pointer}/{key}")
    return payload[key]


def normalize_semgrep(
    payload: dict[str, Any], tool_version: str, target: str
) -> ScanDocument:
    """Normalize stable Semgrep CLI JSON fields without reading source files."""
    root = _require_mapping(payload, "/")
    results = _require_value(root, "results", "")
    _require_value(root, "errors", "")
    _require_value(root, "paths", "")
    if not isinstance(results, list):
        raise SemgrepFormatError("Expected an array at /results")

    findings: list[Finding] = []
    for index, item in enumerate(results):
        pointer = f"/results/{index}"
        result = _require_mapping(item, pointer)
        start = _require_mapping(_require_value(result, "start", pointer), pointer + "/start")
        end = _require_mapping(_require_value(result, "end", pointer), pointer + "/end")
        extra = _require_mapping(_require_value(result, "extra", pointer), pointer + "/extra")

        metadata_value = extra.get("metadata", {})
        metadata = _require_mapping(metadata_value, pointer + "/extra/metadata")
        normalized_metadata = {
            key: value for key, value in metadata.items() if key in _METADATA_FIELDS
        }
        findings.append(
            Finding.create(
                rule_id=_require_value(result, "check_id", pointer),
                severity=extra.get("severity", "unknown"),
                path=_require_value(result, "path", pointer),
                start_line=_require_value(start, "line", pointer + "/start"),
                start_column=start.get("col"),
                end_line=_require_value(end, "line", pointer + "/end"),
                end_column=end.get("col"),
                message=_require_value(extra, "message", pointer + "/extra"),
                code=extra.get("lines"),
                metadata=normalized_metadata,
                raw_reference=pointer,
            )
        )

    return ScanDocument.create(tool_version, target, findings)
