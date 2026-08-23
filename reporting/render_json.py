import json
from dataclasses import asdict
from typing import Any

from agent.models import AnalysisDocument
from reporting.models import SecurityReport
from reporting.render_analysis import analysis_items, evidence_summary
from reporting.risk import order_findings


def report_dict(
    report: SecurityReport, analysis: AnalysisDocument | None = None
) -> dict[str, object]:
    findings: list[dict[str, Any]] = list(report.findings)
    if analysis is not None:
        by_id = analysis_items(analysis)
        findings = [dict(item) for item in order_findings(findings, by_id)]
        for finding in findings:
            analysis_item = by_id.get(finding["id"])
            if analysis_item is not None:
                enriched = dict(analysis_item)
                enriched["evidence_summary"] = evidence_summary(
                    analysis_item.get("evidence")
                )
                finding["_analysis"] = enriched
    return {
        "report_version": "1.0",
        "generated_at": report.generated_at,
        "sources": [asdict(source) for source in report.sources],
        "summary": {"total": len(report.findings), **report.counts},
        "findings": findings,
    }


def render_json(report: SecurityReport) -> str:
    return json.dumps(report_dict(report), ensure_ascii=False, indent=2) + "\n"
