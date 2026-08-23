import json

from reporting.models import SecurityReport


def render_markdown(report: SecurityReport) -> str:
    lines = ["# Security Report", "", f"Generated: {report.generated_at}", "", "## Scan Sources", "", "| Tool | Version | Ruleset | Target |", "| --- | --- | --- | --- |"]
    lines.extend(f"| {s.tool} | {s.tool_version} | {s.ruleset} | {s.target} |" for s in report.sources)
    lines += ["", "## Summary", "", f"Total findings: {len(report.findings)}", "", "| Severity | Count |", "| --- | ---: |"]
    lines.extend(f"| {severity} | {report.counts[severity]} |" for severity in ("error", "warning", "info", "unknown"))
    lines += ["", "## Findings", ""]
    if not report.findings:
        lines.append("No findings.")
    for item in report.findings:
        lines += [f"### [{item['severity']}] {item['rule_id']}", "", f"- Tool: {item['tool']}", f"- Location: {item['path']}:{item['start_line']}", f"- ID: {item['id']}", f"- Message: {item['message']}", f"- Raw reference: {item['raw_reference']}"]
        if item.get("code"):
            lines += ["", "```text", str(item["code"]), "```"]
        if item.get("metadata"):
            lines += ["", f"Metadata: `{json.dumps(item['metadata'], ensure_ascii=False, sort_keys=True)}`"]
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
