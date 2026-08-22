"""Render findings enriched with deterministic analysis items."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from agent.models import AnalysisDocument
from reporting.models import SecurityReport


def _analysis_map(analysis: AnalysisDocument) -> dict[str, dict[str, Any]]:
    return {item.finding_id: item.to_dict() for item in analysis.items}


def render_analysis_json(report: SecurityReport, analysis: AnalysisDocument) -> str:
    """Serialize findings plus analysis into a single enriched JSON document."""
    payload = {
        "generated_at": report.generated_at,
        "sources": [asdict(source) for source in report.sources],
        "counts": report.counts,
        "findings": list(report.findings),
        "analysis": analysis.to_dict(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_analysis_markdown(report: SecurityReport, analysis: AnalysisDocument) -> str:
    """Render an enriched Markdown report merging findings and analysis."""
    by_id = _analysis_map(analysis)
    lines = [
        "# Security Report",
        "",
        f"Generated: {report.generated_at}",
        "",
        "## Scan Sources",
        "",
        "| Tool | Version | Ruleset | Target |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {s.tool} | {s.tool_version} | {s.ruleset} | {s.target} |"
        for s in report.sources
    )
    lines += [
        "",
        "## Summary",
        "",
        f"Total findings: {len(report.findings)}",
        "",
        "| Severity | Count |",
        "| --- | ---: |",
    ]
    lines.extend(
        f"| {severity} | {report.counts[severity]} |"
        for severity in ("error", "warning", "info", "unknown")
    )
    lines += ["", "## Findings", ""]
    if not report.findings:
        lines.append("No findings.")
    for item in report.findings:
        analysis_item = by_id.get(item["id"])
        label = analysis_item["label"] if analysis_item else "unanalyzed"
        lines += [
            f"### [{item['severity']}] {item['rule_id']}",
            "",
            f"- Tool: {item['tool']}",
            f"- Location: {item['path']}:{item['start_line']}",
            f"- ID: {item['id']}",
            f"- Message: {item['message']}",
            f"- Classification: {label}",
        ]
        if item.get("code"):
            lines += ["", "```text", str(item["code"]), "```"]
        if item.get("metadata"):
            lines += [
                "",
                f"Metadata: `{json.dumps(item['metadata'], ensure_ascii=False, sort_keys=True)}`",
            ]
        if analysis_item:
            lines += [
                "",
                f"- Cause: {analysis_item['cause']}",
                f"- Impact: {analysis_item['impact']}",
                f"- Remediation: {analysis_item['remediation']}",
            ]
            if analysis_item.get("references"):
                lines.append(f"- References: {', '.join(analysis_item['references'])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
