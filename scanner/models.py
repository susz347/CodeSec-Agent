"""Stable, tool-neutral security finding data structures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any


_KNOWN_SEVERITIES = {"error", "warning", "info"}


@dataclass(frozen=True)
class Finding:
    """A normalized security finding produced by a scanner."""

    id: str
    tool: str
    rule_id: str
    severity: str
    path: str
    start_line: int
    start_column: int | None
    end_line: int
    end_column: int | None
    message: str
    code: str | None
    metadata: dict[str, Any]
    raw_reference: str

    @classmethod
    def create(
        cls,
        rule_id: str,
        severity: str,
        path: str,
        start_line: int,
        start_column: int | None,
        end_line: int,
        end_column: int | None,
        message: str,
        code: str | None,
        metadata: dict[str, Any],
        raw_reference: str,
        *,
        tool: str = "semgrep",
    ) -> Finding:
        """Create a finding with a deterministic identifier and severity."""
        normalized_severity = severity.lower()
        normalized_metadata = dict(metadata)
        if normalized_severity not in _KNOWN_SEVERITIES:
            normalized_metadata[f"{tool.replace('-', '_')}_severity"] = severity
            normalized_severity = "unknown"

        identifier_source = f"{tool}|{rule_id}|{path}|{start_line}|{start_column}"
        identifier = sha256(identifier_source.encode("utf-8")).hexdigest()[:16]
        return cls(
            id=identifier,
            tool=tool,
            rule_id=rule_id,
            severity=normalized_severity,
            path=path,
            start_line=start_line,
            start_column=start_column,
            end_line=end_line,
            end_column=end_column,
            message=message,
            code=code,
            metadata=normalized_metadata,
            raw_reference=raw_reference,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize this finding to the versioned output contract."""
        return {
            "id": self.id,
            "tool": self.tool,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "path": self.path,
            "start_line": self.start_line,
            "start_column": self.start_column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "message": self.message,
            "code": self.code,
            "metadata": self.metadata,
            "raw_reference": self.raw_reference,
        }


@dataclass(frozen=True)
class ScanDocument:
    """The top-level normalized findings document."""

    schema_version: str
    scan: dict[str, str]
    findings: tuple[Finding, ...]

    @classmethod
    def create(
        cls,
        tool_version: str,
        target: str,
        findings: list[Finding],
        *,
        tool: str = "semgrep",
        ruleset: str = "p/security-audit",
    ) -> ScanDocument:
        """Create a document with Semgrep-specific scan metadata."""
        started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return cls(
            schema_version="1.0",
            scan={
                "tool": tool,
                "tool_version": tool_version,
                "ruleset": ruleset,
                "target": target,
                "started_at": started_at,
            },
            findings=tuple(findings),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete normalized findings document."""
        return {
            "schema_version": self.schema_version,
            "scan": self.scan,
            "findings": [finding.to_dict() for finding in self.findings],
        }
