from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2, "unknown": 3}

@dataclass(frozen=True)
class ScanSource:
    tool: str
    tool_version: str
    ruleset: str
    target: str
    started_at: str

@dataclass(frozen=True)
class SecurityReport:
    generated_at: str
    sources: tuple[ScanSource, ...]
    findings: tuple[dict[str, Any], ...]
    counts: dict[str, int]

    @classmethod
    def create(cls, sources: list[ScanSource], findings: list[dict[str, Any]]) -> SecurityReport:
        counts = {name: 0 for name in SEVERITY_ORDER}
        for item in findings:
            counts[item["severity"]] += 1
        ordered = sorted(findings, key=lambda item: (SEVERITY_ORDER[item["severity"]], item["tool"], item["path"], item["start_line"], item["id"]))
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return cls(timestamp, tuple(sources), tuple(ordered), counts)
