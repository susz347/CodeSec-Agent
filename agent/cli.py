"""Generate deterministic security analysis from normalized finding documents."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from agent.models import AnalysisDocument, AnalysisFormatError
from agent.security_reviewer import analyze


def _load_findings(paths: Sequence[Path]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AnalysisFormatError(f"Cannot read finding document: {path}") from error
        if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
            raise AnalysisFormatError(f"Unsupported finding schema: {path}")
        items = payload.get("findings")
        if not isinstance(items, list):
            raise AnalysisFormatError(f"Missing findings array: {path}")
        findings.extend(item for item in items if isinstance(item, dict))
    return findings


def render_analysis_markdown(document: AnalysisDocument) -> str:
    lines = [
        "# Security Analysis",
        "",
        f"Generated: {document.generated_at}",
        f"Backend: {document.backend}",
        "",
        f"Total items: {len(document.items)}",
        "",
    ]
    if not document.items:
        lines.append("No findings analyzed.")
    for item in document.items:
        lines += [
            f"### [{item.label}] {item.title}",
            "",
            f"- Finding: `{item.finding_id}`",
            f"- Cause: {item.cause}",
            f"- Impact: {item.impact}",
            f"- Remediation: {item.remediation}",
        ]
        if item.references:
            lines.append(f"- References: {', '.join(item.references)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _write_outputs(pairs: Sequence[tuple[Path, str]]) -> None:
    temporary: list[tuple[Path, Path]] = []
    try:
        for output, content in pairs:
            temp = output.with_name(f".{output.name}.tmp")
            temp.write_text(content, encoding="utf-8")
            temporary.append((temp, output))
        for temp, output in temporary:
            temp.replace(output)
    finally:
        for temp, _ in temporary:
            temp.unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic security analysis.")
    parser.add_argument("--input", action="append", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        findings = _load_findings(arguments.input)
        document = analyze({"schema_version": "1.0", "findings": findings})
        arguments.output_dir.mkdir(parents=True, exist_ok=True)
        json_output = arguments.output_dir / "analysis.json"
        markdown_output = arguments.output_dir / "analysis.md"
        _write_outputs(
            [
                (json_output, json.dumps(document.to_dict(), ensure_ascii=False, indent=2) + "\n"),
                (markdown_output, render_analysis_markdown(document)),
            ]
        )
    except (AnalysisFormatError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    print(json_output)
    print(markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
