"""Stable analysis data contract for the security review agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

LABELS = ("confirmed", "suspicious", "possible_false_positive")


class AnalysisFormatError(ValueError):
    """Raised when an analysis document cannot be parsed or validated."""


@dataclass(frozen=True)
class AnalysisItem:
    """A single finding with an explanation, classification, and remediation."""

    finding_id: str
    label: str
    title: str
    cause: str
    impact: str
    remediation: str
    references: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.label not in LABELS:
            raise AnalysisFormatError(f"Unknown analysis label: {self.label}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "label": self.label,
            "title": self.title,
            "cause": self.cause,
            "impact": self.impact,
            "remediation": self.remediation,
            "references": list(self.references),
        }


@dataclass(frozen=True)
class AnalysisDocument:
    """The top-level analysis output document."""

    schema_version: str
    generated_at: str
    backend: str
    items: tuple[AnalysisItem, ...]

    @classmethod
    def create(cls, backend: str, items: list[AnalysisItem]) -> AnalysisDocument:
        """Create a document with a deterministic timestamp."""
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return cls("1.0", timestamp, backend, tuple(items))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "backend": self.backend,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AnalysisDocument:
        """Parse a serialized analysis document and validate its labels."""
        if not isinstance(payload, dict):
            raise AnalysisFormatError("Expected an object at /")
        if payload.get("schema_version") != "1.0":
            raise AnalysisFormatError("Unsupported analysis schema")
        items_value = payload.get("items")
        if not isinstance(items_value, list):
            raise AnalysisFormatError("Expected an array at /items")
        items: list[AnalysisItem] = []
        for index, item in enumerate(items_value):
            if not isinstance(item, dict):
                raise AnalysisFormatError(f"Expected an object at /items/{index}")
            try:
                items.append(
                    AnalysisItem(
                        finding_id=item["finding_id"],
                        label=item["label"],
                        title=item.get("title", ""),
                        cause=item.get("cause", ""),
                        impact=item.get("impact", ""),
                        remediation=item.get("remediation", ""),
                        references=tuple(str(r) for r in item.get("references", [])),
                    )
                )
            except KeyError as error:
                raise AnalysisFormatError(
                    f"Missing field at /items/{index}: {error.args[0]}"
                ) from error
        return cls(
            schema_version="1.0",
            generated_at=str(payload.get("generated_at", "")),
            backend=str(payload.get("backend", "unknown")),
            items=tuple(items),
        )
