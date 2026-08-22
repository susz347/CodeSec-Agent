"""Convert npm audit JSON into normalized findings."""

from __future__ import annotations

from typing import Any

from scanner.models import Finding, ScanDocument


_SEVERITIES = {"critical": "error", "high": "error", "moderate": "warning", "low": "info", "info": "info"}


class NpmAuditFormatError(ValueError):
    """Raised when npm audit JSON cannot be normalized safely."""


def _require(payload: dict[str, Any], key: str, pointer: str) -> Any:
    if key not in payload:
        raise NpmAuditFormatError(f"Missing required field at {pointer}/{key}")
    return payload[key]


def normalize_npm_audit(payload: dict[str, Any], tool_version: str, target: str) -> ScanDocument:
    if not isinstance(payload, dict):
        raise NpmAuditFormatError("Expected an object at /")
    vulnerabilities = _require(payload, "vulnerabilities", "")
    _require(payload, "metadata", "")
    if not isinstance(vulnerabilities, dict):
        raise NpmAuditFormatError("Expected an object at /vulnerabilities")
    findings: list[Finding] = []
    for key, item in vulnerabilities.items():
        pointer = f"/vulnerabilities/{key.replace('~', '~0').replace('/', '~1')}"
        if not isinstance(item, dict):
            raise NpmAuditFormatError(f"Expected an object at {pointer}")
        name = _require(item, "name", pointer)
        severity = _require(item, "severity", pointer)
        audit_range = _require(item, "range", pointer)
        via = _require(item, "via", pointer)
        if not isinstance(via, list):
            raise NpmAuditFormatError(f"Expected an array at {pointer}/via")
        cwe: list[str] = []
        references: list[str] = []
        titles: list[str] = []
        for advisory in via:
            if isinstance(advisory, dict):
                cwe.extend(value for value in advisory.get("cwe", []) if isinstance(value, str))
                if isinstance(advisory.get("url"), str): references.append(advisory["url"])
                if isinstance(advisory.get("title"), str): titles.append(advisory["title"])
        metadata: dict[str, Any] = {"category": "dependency", "npm_audit_severity": severity}
        if cwe: metadata["cwe"] = list(dict.fromkeys(cwe))
        if references: metadata["references"] = list(dict.fromkeys(references))
        findings.append(Finding.create(rule_id=f"npm-audit/{key}", severity=_SEVERITIES.get(str(severity).lower(), "unknown"), path="package-lock.json", start_line=1, start_column=None, end_line=1, end_column=None, message=titles[0] if titles else f"{name} is affected by {audit_range}", code=None, metadata=metadata, raw_reference=pointer, tool="npm-audit"))
    return ScanDocument.create(tool_version, target, findings, tool="npm-audit", ruleset="npm-advisory-database")
