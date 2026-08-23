"""Versioned local baseline and human-triage records for security findings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable

_SCHEMA_VERSION = "1.0"
_RESOLUTIONS = {"true_positive", "false_positive", "accepted_risk", "needs_fix"}


class TriageFormatError(ValueError):
    """Raised when a triage document is invalid."""


@dataclass(frozen=True)
class BaselineComparison:
    status_by_id: dict[str, str]
    resolved: tuple[str, ...]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _text(value: object) -> str:
    return " ".join(str(value or "").split())


def fingerprint(finding: dict[str, object]) -> str:
    """Return a stable fingerprint that intentionally excludes line numbers."""
    parts = (
        _text(finding.get("tool")).lower(),
        _text(finding.get("rule_id")).lower(),
        _text(finding.get("path")).replace("\\", "/").lower(),
        _text(finding.get("code") or finding.get("message")),
    )
    return sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]


def _baseline_entry(finding: dict[str, object]) -> dict[str, str]:
    return {
        "fingerprint": fingerprint(finding),
        "tool": _text(finding.get("tool")),
        "rule_id": _text(finding.get("rule_id")),
        "path": _text(finding.get("path")).replace("\\", "/"),
    }


def build_baseline(findings: Iterable[dict[str, object]]) -> dict[str, Any]:
    entries = {_baseline_entry(finding)["fingerprint"]: _baseline_entry(finding) for finding in findings}
    return {
        "schema_version": _SCHEMA_VERSION,
        "baseline": {"generated_at": _now(), "findings": list(entries.values())},
        "dispositions": [],
    }


def _baseline_findings(document: dict[str, Any]) -> list[dict[str, Any]]:
    if document.get("schema_version") != _SCHEMA_VERSION:
        raise TriageFormatError("Unsupported triage schema")
    baseline = document.get("baseline")
    if not isinstance(baseline, dict) or not isinstance(baseline.get("findings"), list):
        raise TriageFormatError("Missing baseline findings")
    return [entry for entry in baseline["findings"] if isinstance(entry, dict)]


def compare_findings(
    findings: Iterable[dict[str, object]], document: dict[str, Any]
) -> BaselineComparison:
    baseline = {str(entry.get("fingerprint", "")) for entry in _baseline_findings(document)}
    current = list(findings)
    current_fingerprints = {fingerprint(finding) for finding in current}
    return BaselineComparison(
        status_by_id={
            str(finding["id"]): "existing" if fingerprint(finding) in baseline else "new"
            for finding in current
        },
        resolved=tuple(sorted(baseline - current_fingerprints)),
    )


def add_disposition(
    document: dict[str, Any],
    *,
    fingerprint: str,
    resolution: str,
    reviewer: str,
    machine_label: str,
    note: str = "",
) -> dict[str, Any]:
    entries = _baseline_findings(document)
    if resolution not in _RESOLUTIONS:
        raise TriageFormatError(f"Unsupported resolution: {resolution}")
    entry = next((item for item in entries if item.get("fingerprint") == fingerprint), None)
    if entry is None:
        raise TriageFormatError(f"Unknown baseline fingerprint: {fingerprint}")
    dispositions = [
        item for item in document.get("dispositions", [])
        if isinstance(item, dict) and item.get("fingerprint") != fingerprint
    ]
    dispositions.append(
        {
            "fingerprint": fingerprint,
            "resolution": resolution,
            "reviewer": _text(reviewer),
            "machine_label": _text(machine_label),
            "note": _text(note),
            "reviewed_at": _now(),
            "tool": entry.get("tool", ""),
            "rule_id": entry.get("rule_id", ""),
        }
    )
    return {**document, "dispositions": dispositions}


def statistics(document: dict[str, Any]) -> dict[str, Any]:
    _baseline_findings(document)
    by_rule: dict[str, dict[str, int]] = {}
    for item in document.get("dispositions", []):
        if not isinstance(item, dict):
            continue
        key = f"{item.get('tool', '')}:{item.get('rule_id', '')}"
        group = by_rule.setdefault(key, {})
        resolution = str(item.get("resolution", "unknown"))
        group[resolution] = group.get(resolution, 0) + 1
    return {"total": sum(sum(group.values()) for group in by_rule.values()), "by_rule": by_rule}


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TriageFormatError(f"Cannot read triage document: {path}") from error
    if not isinstance(value, dict):
        raise TriageFormatError("Expected a triage object")
    _baseline_findings(value)
    return value


def save(path: Path, document: dict[str, Any]) -> None:
    _baseline_findings(document)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
