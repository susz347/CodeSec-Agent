"""Deterministic triage ordering for security findings.

Orders findings by the signals the agent already produces — severity,
classification label, and PR diff status — so human reviewers see the most
actionable items first (confirmed + changed + high severity). This is
*ordering*, not a calibrated numeric risk score: it uses only deterministic
labels and introduces no baseline or statistical modeling. Risk *scoring* must
wait for real triage data (see the roadmap note on baseline calibration).
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from reporting.models import SEVERITY_ORDER

LABEL_ORDER = {"confirmed": 0, "suspicious": 1, "possible_false_positive": 2}
DIFF_ORDER = {"changed": 0, "unknown": 1, "unchanged": 2}


def _int(value: Any, default: int = 1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def risk_key(
    finding: Mapping[str, Any], analysis_item: Mapping[str, Any] | None
) -> tuple[int, int, int, str, str, int, str]:
    """Return a sort key that ranks the most actionable finding first."""
    label = analysis_item.get("label") if analysis_item else None
    diff_status = (
        analysis_item.get("diff_status", "unknown") if analysis_item else "unknown"
    )
    severity = str(finding.get("severity", "unknown"))
    return (
        LABEL_ORDER.get(label, 3),
        DIFF_ORDER.get(diff_status, 1),
        SEVERITY_ORDER.get(severity, 3),
        str(finding.get("tool", "")),
        str(finding.get("path", "")),
        _int(finding.get("start_line")),
        str(finding.get("id", "")),
    )


def order_findings(
    findings: Sequence[Mapping[str, Any]],
    analysis_items: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[Mapping[str, Any]]:
    """Return findings sorted by triage priority.

    ``analysis_items`` maps a finding ``id`` to its ``AnalysisItem.to_dict()``.
    Findings without an analysis item sort last (unanalyzed) and fall back to
    severity order. With no analysis at all, this degrades to severity order.
    """
    items = analysis_items or {}
    return sorted(
        findings,
        key=lambda finding: risk_key(
            finding, items.get(str(finding.get("id", "")))
        ),
    )
