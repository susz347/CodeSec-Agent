from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from reporting.load_findings import ReportInputError, load_documents
from reporting.render_json import render_json
from reporting.render_markdown import render_markdown


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate local security reports.")
    parser.add_argument("--input", action="append", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        report = load_documents(arguments.input)
        json_content, markdown_content = render_json(report), render_markdown(report)
        arguments.output_dir.mkdir(parents=True, exist_ok=True)
        json_output = arguments.output_dir / "security-report.json"
        markdown_output = arguments.output_dir / "security-report.md"
        json_temp = arguments.output_dir / ".security-report.json.tmp"
        markdown_temp = arguments.output_dir / ".security-report.md.tmp"
        try:
            json_temp.write_text(json_content, encoding="utf-8")
            markdown_temp.write_text(markdown_content, encoding="utf-8")
            json_temp.replace(json_output)
            markdown_temp.replace(markdown_output)
        finally:
            json_temp.unlink(missing_ok=True)
            markdown_temp.unlink(missing_ok=True)
    except (ReportInputError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    print(json_output)
    print(markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
