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
    for item in items:
        label = str(item.get("label", "unanalyzed"))
        label_counts[label] = label_counts.get(label, 0) + 1
        status = str(item.get("diff_status", "unknown"))
        diff_counts[status] = diff_counts.get(status, 0) + 1

    rule_ids = sorted({str(f["rule_id"]) for f in findings if f.get("rule_id")})
    paths = sorted({str(f["path"]) for f in findings if f.get("path")})

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
    if rule_ids:
        lines.append("- Rules: " + ", ".join(f"`{rule}`" for rule in rule_ids))
    if paths:
        lines.append("- Paths: " + ", ".join(f"`{path}`" for path in paths))
    if int(counts.get("error", 0)) > 0:
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
