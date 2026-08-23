from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reporting.models import SEVERITY_ORDER, ScanSource, SecurityReport

class ReportInputError(ValueError):
    """Raised when a normalized finding document is invalid."""

def load_documents(paths: list[Path]) -> SecurityReport:
    sources: list[ScanSource] = []
    findings: list[dict[str, Any]] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ReportInputError(f"Cannot read finding document: {path}") from error
        if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
            raise ReportInputError(f"Unsupported finding schema: {path}")
        scan, items = payload.get("scan"), payload.get("findings")
        if not isinstance(scan, dict) or not isinstance(items, list):
            raise ReportInputError(f"Missing scan or findings: {path}")
        try:
            sources.append(ScanSource(**{key: scan[key] for key in ("tool", "tool_version", "ruleset", "target", "started_at")}))
        except KeyError as error:
            raise ReportInputError(f"Missing scan field: {error.args[0]}") from error
        for index, item in enumerate(items):
            required = ("id", "tool", "rule_id", "severity", "path", "start_line", "message", "metadata", "raw_reference")
            if not isinstance(item, dict) or any(key not in item for key in required) or item.get("severity") not in SEVERITY_ORDER:
                raise ReportInputError(f"Invalid finding /findings/{index}")
            findings.append(dict(item))
    return SecurityReport.create(sources, findings)
