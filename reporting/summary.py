"""Render a compact, non-blocking PR summary from an enriched report payload.

The summary deliberately contains only counts, rule IDs, paths, and an artifact
link. It never includes source snippets or credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

_LABELS = ("confirmed", "suspicious", "possible_false_positive")


def render_pr_summary(payload: dict[str, Any], artifacts_url: str = "") -> str:
    counts = payload.get("counts", {}) or {}
    findings = payload.get("findings", []) or []
    items = (payload.get("analysis") or {}).get("items", []) or []

    label_counts: dict[str, int] = {}
    diff_counts: dict[str, int] = {}
    baseline_counts: dict[str, int] = {}
    for item in items:
        label = str(item.get("label", "unanalyzed"))
        label_counts[label] = label_counts.get(label, 0) + 1
        status = str(item.get("diff_status", "unknown"))
        diff_counts[status] = diff_counts.get(status, 0) + 1
        baseline = str(item.get("baseline_status", "unknown"))
        baseline_counts[baseline] = baseline_counts.get(baseline, 0) + 1

    items_by_id = {str(item.get("finding_id", "")): item for item in items}
    new_findings = [
        finding for finding in findings
        if items_by_id.get(str(finding.get("id", "")), {}).get("baseline_status") == "new"
    ]
    baseline_is_available = baseline_counts.get("new", 0) + baseline_counts.get("existing", 0) > 0
    summary_findings = new_findings if baseline_is_available else findings
    rule_ids = sorted({str(f["rule_id"]) for f in summary_findings if f.get("rule_id")})
    paths = sorted({str(f["path"]) for f in summary_findings if f.get("path")})

    lines = [
        "## Security Scan Summary",
        "",
        f"- Total findings: {len(findings)}",
        "- Severity: "
        + ", ".join(
            f"{severity}={counts.get(severity, 0)}"
            for severity in ("error", "warning", "info", "unknown")
        ),
    ]
    if items:
        lines.append(
            "- Classification: "
            + ", ".join(f"{label}={label_counts.get(label, 0)}" for label in _LABELS)
        )
    if diff_counts.get("changed", 0) + diff_counts.get("unchanged", 0) > 0:
        lines.append(
            "- Diff: "
            + ", ".join(
                f"{status}={diff_counts.get(status, 0)}"
                for status in ("changed", "unchanged", "unknown")
            )
        )
    if baseline_counts.get("new", 0) + baseline_counts.get("existing", 0) > 0:
        lines.append(
            "- Baseline: "
            + ", ".join(
                f"{status}={baseline_counts.get(status, 0)}"
                for status in ("new", "existing", "unknown")
            )
        )
    if rule_ids:
        lines.append("- Rules: " + ", ".join(f"`{rule}`" for rule in rule_ids))
    if paths:
        lines.append("- Paths: " + ", ".join(f"`{path}`" for path in paths))
    high_severity = (
        any(str(finding.get("severity", "")) == "error" for finding in summary_findings)
        if baseline_is_available
        else int(counts.get("error", 0)) > 0
    )
    if high_severity:
        lines.append(
            "- [!] High-severity findings present; recommend human review before merging."
        )
    if artifacts_url:
        lines.append(f"- Artifacts: {artifacts_url}")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a compact PR summary.")
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--artifacts-url", default="")
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        payload = json.loads(arguments.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot read report: {arguments.report}", file=sys.stderr)
        return 1
    arguments.output.write_text(
        render_pr_summary(payload, arguments.artifacts_url), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
