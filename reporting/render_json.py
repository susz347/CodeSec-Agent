import json
from dataclasses import asdict

from reporting.models import SecurityReport


def report_dict(report: SecurityReport) -> dict[str, object]:
    return {"report_version": "1.0", "generated_at": report.generated_at, "sources": [asdict(source) for source in report.sources], "summary": {"total": len(report.findings), **report.counts}, "findings": list(report.findings)}


def render_json(report: SecurityReport) -> str:
    return json.dumps(report_dict(report), ensure_ascii=False, indent=2) + "\n"
