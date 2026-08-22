from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from reporting.errors import ReportRenderError
from reporting.load_findings import ReportInputError, load_documents
from reporting.models import SecurityReport
from reporting.render_json import render_json
from reporting.render_markdown import render_markdown

_FORMAT_ORDER = ("json", "markdown", "xlsx", "docx", "pdf")
_DEFAULT_FORMATS = ("json", "markdown")
_SUFFIXES = {
    "json": "json",
    "markdown": "md",
    "xlsx": "xlsx",
    "docx": "docx",
    "pdf": "pdf",
}


def _selected_formats(values: list[str] | None) -> tuple[str, ...]:
    if not values:
        return _DEFAULT_FORMATS
    if "all" in values:
        return _FORMAT_ORDER
    return tuple(name for name in _FORMAT_ORDER if name in values)


def _render_format(report: SecurityReport, name: str) -> bytes:
    if name == "json":
        return render_json(report).encode("utf-8")
    if name == "markdown":
        return render_markdown(report).encode("utf-8")
    try:
        if name == "xlsx":
            from reporting.render_excel import render_excel

            return render_excel(report)
        if name == "docx":
            from reporting.render_docx import render_docx

            return render_docx(report)
        if name == "pdf":
            from reporting.render_pdf import render_pdf

            return render_pdf(report)
    except ModuleNotFoundError as error:
        raise ReportRenderError(
            f"{name} rendering dependencies are missing; "
            "run: python -m pip install -r requirements-dev.txt"
        ) from error
    raise ReportRenderError(f"Unsupported report format: {name}")


def _commit_outputs(pairs: Sequence[tuple[Path, Path]]) -> None:
    backups: list[tuple[Path, Path]] = []
    committed: list[Path] = []
    try:
        for _, output in pairs:
            backup = output.with_name(f".{output.name}.bak")
            backup.unlink(missing_ok=True)
            if output.exists():
                output.replace(backup)
                backups.append((backup, output))
        for temporary, output in pairs:
            temporary.replace(output)
            committed.append(output)
    except OSError:
        for output in committed:
            output.unlink(missing_ok=True)
        for backup, output in backups:
            if backup.exists():
                backup.replace(output)
        raise
    else:
        for backup, _ in backups:
            try:
                backup.unlink(missing_ok=True)
            except OSError:
                pass


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate local security reports.")
    parser.add_argument("--input", action="append", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--format",
        action="append",
        choices=(*_FORMAT_ORDER, "all"),
        dest="formats",
    )
    arguments = parser.parse_args(argv)
    try:
        report = load_documents(arguments.input)
        formats = _selected_formats(arguments.formats)
        rendered = {name: _render_format(report, name) for name in formats}
        arguments.output_dir.mkdir(parents=True, exist_ok=True)
        pairs: list[tuple[Path, Path]] = []
        try:
            for name in formats:
                suffix = _SUFFIXES[name]
                output = arguments.output_dir / f"security-report.{suffix}"
                temporary = arguments.output_dir / f".security-report.{suffix}.tmp"
                pairs.append((temporary, output))
                temporary.write_bytes(rendered[name])
            _commit_outputs(pairs)
        finally:
            for temporary, _ in pairs:
                temporary.unlink(missing_ok=True)
    except (ReportInputError, ReportRenderError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    for _, output in pairs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
