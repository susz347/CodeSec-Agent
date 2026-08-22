"""LLM review contract: request/response schemas and validation.

The contract pins what a model may return and makes its evidence citations
machine-verifiable. A model must not assert a verdict in prose; it returns
structured fields and, for a ``confirmed`` verdict, cites specific source lines
(``evidence_refs``) that fall inside the context we actually sent it. The
transport (``LlmClient``) is a protocol only; no real model call is wired here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from agent.models import LABELS


class LlmFormatError(ValueError):
    """Raised when an LLM response violates the review contract."""


@dataclass(frozen=True)
class EvidenceRef:
    """A machine-verifiable citation to a source location."""

    path: str
    start_line: int
    end_line: int

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "start_line": self.start_line, "end_line": self.end_line}


@dataclass(frozen=True)
class LlmVerdict:
    """A single finding verdict returned by the model."""

    finding_id: str
    label: str
    title: str
    cause: str
    impact: str
    remediation: str
    references: tuple[str, ...]
    evidence_refs: tuple[EvidenceRef, ...]


class LlmClient(Protocol):
    """Transport for calling a language model. Not implemented here."""

    def complete(self, request: dict[str, Any]) -> dict[str, Any]: ...


def build_llm_request(
    findings: Sequence[dict[str, Any]],
    evidence: Mapping[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the request payload sent to the model.

    Each finding includes its matched ``code`` and, when available, the local
    ``context`` window the model is allowed to cite (via ``evidence_refs``).
    """
    evidence = evidence or {}
    return {
        "schema_version": "1.0",
        "findings": [
            {
                "finding_id": str(finding["id"]),
                "rule_id": finding.get("rule_id", ""),
                "severity": finding.get("severity", ""),
                "path": finding.get("path", ""),
                "start_line": finding.get("start_line", 1),
                "end_line": finding.get("end_line", finding.get("start_line", 1)),
                "message": finding.get("message", ""),
                "code": finding.get("code"),
                "context": evidence.get(str(finding["id"])),
            }
            for finding in findings
        ],
    }


def _verifiable_span(
    finding: dict[str, Any], evidence: dict[str, Any] | None
) -> tuple[int, int]:
    """Return the 1-based line span the model was shown and may cite."""
    if evidence:
        return int(evidence.get("start_line", 1)), int(evidence.get("end_line", 1))
    start = int(finding.get("start_line", 1))
    return start, int(finding.get("end_line", start))


def parse_llm_response(
    payload: dict[str, Any],
    findings: Sequence[dict[str, Any]],
    evidence: Mapping[str, dict[str, Any]] | None = None,
) -> tuple[LlmVerdict, ...]:
    """Validate and parse a model response into verdicts.

    Raises ``LlmFormatError`` on any contract violation, including evidence
    citations that fall outside the context we sent or reference another path.
    """
    evidence = evidence or {}
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        raise LlmFormatError("Expected a schema 1.0 object at /")
    items_value = payload.get("items")
    if not isinstance(items_value, list):
        raise LlmFormatError("Expected an array at /items")

    finding_by_id = {str(f["id"]): f for f in findings if isinstance(f, dict)}
    verdicts: list[LlmVerdict] = []
    for index, item in enumerate(items_value):
        if not isinstance(item, dict):
            raise LlmFormatError(f"Expected an object at /items/{index}")
        finding_id = str(item.get("finding_id", ""))
        if finding_id not in finding_by_id:
            raise LlmFormatError(f"Unknown finding_id at /items/{index}: {finding_id}")
        label = str(item.get("label", ""))
        if label not in LABELS:
            raise LlmFormatError(f"Unknown label at /items/{index}: {label}")
        refs = _parse_evidence_refs(
            item.get("evidence_refs", []),
            finding_by_id[finding_id],
            evidence.get(finding_id),
            index,
        )
        if label == "confirmed" and not refs:
            raise LlmFormatError(
                f"Confirmed verdict at /items/{index} must cite evidence_refs"
            )
        verdicts.append(
            LlmVerdict(
                finding_id=finding_id,
                label=label,
                title=str(item.get("title", "")),
                cause=str(item.get("cause", "")),
                impact=str(item.get("impact", "")),
                remediation=str(item.get("remediation", "")),
                references=tuple(str(r) for r in item.get("references", [])),
                evidence_refs=refs,
            )
        )
    return tuple(verdicts)


def _parse_evidence_refs(
    value: Any,
    finding: dict[str, Any],
    evidence: dict[str, Any] | None,
    item_index: int,
) -> tuple[EvidenceRef, ...]:
    if not isinstance(value, list):
        raise LlmFormatError(f"Expected an array at /items/{item_index}/evidence_refs")
    start, end = _verifiable_span(finding, evidence)
    refs: list[EvidenceRef] = []
    for ref_index, ref in enumerate(value):
        pointer = f"/items/{item_index}/evidence_refs/{ref_index}"
        if not isinstance(ref, dict):
            raise LlmFormatError(f"Expected an object at {pointer}")
        path = ref.get("path")
        ref_start = ref.get("start_line")
        ref_end = ref.get("end_line")
        if not isinstance(path, str) or not isinstance(ref_start, int) or not isinstance(ref_end, int):
            raise LlmFormatError(f"Invalid evidence ref fields at {pointer}")
        if path != str(finding.get("path", "")):
            raise LlmFormatError(f"Evidence ref path mismatch at {pointer}")
        if ref_start > ref_end or ref_start < start or ref_end > end:
            raise LlmFormatError(f"Evidence ref out of verifiable range at {pointer}")
        refs.append(EvidenceRef(path, ref_start, ref_end))
    return tuple(refs)
