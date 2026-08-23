"""Deterministic security analysis engine with a pluggable LLM backend."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from agent.knowledge import HIGH_CONFIDENCE, lookup, signature
from agent.llm import LlmClient, build_llm_request, parse_llm_response
from agent.models import AnalysisDocument, AnalysisFormatError, AnalysisItem

_SEVERITY_LABEL = {
    "error": "confirmed",
    "warning": "suspicious",
    "info": "possible_false_positive",
    "unknown": "possible_false_positive",
}

_TEST_DIRS = {"test", "tests", "spec", "__tests__"}


def _is_test_path(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    parts = lowered.split("/")
    if any(part in _TEST_DIRS for part in parts[:-1]):
        return True
    name = parts[-1]
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or name.startswith("test.")
        or ".spec." in name
    )


def _is_commented(code: str | None) -> bool:
    if not code:
        return False
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    if not lines:
        return False
    return all(line.startswith(("#", "//", "/*", "*", "<!--")) for line in lines)


def _downgrade(label: str) -> str:
    return "suspicious" if label == "confirmed" else "possible_false_positive"


def _classify(finding: dict[str, Any]) -> str:
    tool = str(finding.get("tool", "")).lower()
    severity = str(finding.get("severity", "")).lower()
    path = str(finding.get("path", ""))
    code = finding.get("code")

    label = _SEVERITY_LABEL.get(severity, "possible_false_positive")
    is_test = _is_test_path(path)

    if is_test:
        label = _downgrade(label)
    if tool != "npm-audit" and not code:
        label = "suspicious" if label == "confirmed" else "possible_false_positive"
    if signature(finding) in HIGH_CONFIDENCE and code and not is_test:
        label = "confirmed"
    if _is_commented(code):
        label = "possible_false_positive"
    return label


def _references(knowledge: Any) -> tuple[str, ...]:
    return tuple(value for value in (knowledge.cwe, knowledge.owasp) if value)


class ReviewerBackend(Protocol):
    """A pluggable analysis backend."""

    backend_name: str

    def analyze(
        self,
        findings: Sequence[dict[str, Any]],
        *,
        diff_statuses: Mapping[str, str] | None = None,
        baseline_statuses: Mapping[str, str] | None = None,
        evidence: Mapping[str, dict[str, Any]] | None = None,
    ) -> AnalysisDocument: ...


class DeterministicReviewer:
    """Rule-based reviewer that needs no model and is fully offline."""

    backend_name = "deterministic"

    def analyze(
        self,
        findings: Sequence[dict[str, Any]],
        *,
        diff_statuses: Mapping[str, str] | None = None,
        baseline_statuses: Mapping[str, str] | None = None,
        evidence: Mapping[str, dict[str, Any]] | None = None,
    ) -> AnalysisDocument:
        diff_statuses = diff_statuses or {}
        baseline_statuses = baseline_statuses or {}
        evidence = evidence or {}
        items = [
            self._analyze_finding(
                finding,
                diff_status=diff_statuses.get(str(finding["id"]), "unknown"),
                baseline_status=baseline_statuses.get(str(finding["id"]), "unknown"),
                evidence=evidence.get(str(finding["id"])),
            )
            for finding in findings
        ]
        return AnalysisDocument.create(self.backend_name, items)

    def _analyze_finding(
        self,
        finding: dict[str, Any],
        *,
        diff_status: str,
        baseline_status: str,
        evidence: dict[str, Any] | None,
    ) -> AnalysisItem:
        knowledge = lookup(finding)
        return AnalysisItem(
            finding_id=str(finding["id"]),
            label=_classify(finding),
            title=knowledge.title,
            cause=knowledge.cause or str(finding.get("message", "")),
            impact=knowledge.impact,
            remediation=knowledge.remediation,
            references=_references(knowledge),
            diff_status=diff_status,
            baseline_status=baseline_status,
            evidence=evidence,
        )


class LlmReviewer:
    """LLM backend that delegates to a pluggable client and validates the contract.

    No real model call is wired here: a caller must supply an ``LlmClient``.
    Findings the model does not cover fall back to deterministic analysis, so a
    partial or failed response never silently drops a finding.
    """

    backend_name = "deepseek"

    def __init__(self, client: LlmClient | None = None) -> None:
        self._client = client

    def analyze(
        self,
        findings: Sequence[dict[str, Any]],
        *,
        diff_statuses: Mapping[str, str] | None = None,
        baseline_statuses: Mapping[str, str] | None = None,
        evidence: Mapping[str, dict[str, Any]] | None = None,
    ) -> AnalysisDocument:
        if self._client is None:
            raise NotImplementedError(
                "LlmReviewer requires an LlmClient; no real DeepSeek call is wired."
            )
        diff_statuses = diff_statuses or {}
        baseline_statuses = baseline_statuses or {}
        evidence = evidence or {}
        payload = self._client.complete(build_llm_request(findings, evidence))
        verdicts = parse_llm_response(payload, findings, evidence)
        verdict_by_id = {verdict.finding_id: verdict for verdict in verdicts}
        fallback = DeterministicReviewer()
        items = [
            self._to_item(
                finding,
                verdict_by_id.get(str(finding["id"])),
                diff_statuses.get(str(finding["id"]), "unknown"),
                baseline_statuses.get(str(finding["id"]), "unknown"),
                evidence.get(str(finding["id"])),
                fallback,
            )
            for finding in findings
        ]
        return AnalysisDocument.create(self.backend_name, items)

    def _to_item(
        self,
        finding: dict[str, Any],
        verdict: Any,
        diff_status: str,
        baseline_status: str,
        context: dict[str, Any] | None,
        fallback: DeterministicReviewer,
    ) -> AnalysisItem:
        if verdict is None:
            return fallback._analyze_finding(
                finding,
                diff_status=diff_status,
                baseline_status=baseline_status,
                evidence=context,
            )
        return AnalysisItem(
            finding_id=str(finding["id"]),
            label=verdict.label,
            title=verdict.title,
            cause=verdict.cause,
            impact=verdict.impact,
            remediation=verdict.remediation,
            references=verdict.references,
            diff_status=diff_status,
            baseline_status=baseline_status,
            evidence=context,
            evidence_refs=tuple(ref.to_dict() for ref in verdict.evidence_refs),
        )


def analyze(
    document: dict[str, Any],
    backend: ReviewerBackend | None = None,
    *,
    diff_statuses: Mapping[str, str] | None = None,
    baseline_statuses: Mapping[str, str] | None = None,
    evidence: Mapping[str, dict[str, Any]] | None = None,
) -> AnalysisDocument:
    """Analyze a normalized finding document (schema 1.0) into an analysis document."""
    findings = document.get("findings")
    if not isinstance(findings, list):
        raise AnalysisFormatError("Expected an array at /findings")
    reviewer = backend or DeterministicReviewer()
    return reviewer.analyze(
        [item for item in findings if isinstance(item, dict)],
        diff_statuses=diff_statuses,
        baseline_statuses=baseline_statuses,
        evidence=evidence,
    )
