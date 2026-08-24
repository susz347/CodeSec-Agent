"""Run the pinned Semgrep CLI and write local scan artifacts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from scanner.normalize_semgrep import SemgrepFormatError, normalize_semgrep


RULESET = "p/security-audit"
SEMGREP_VERSION = "1.163.0"


class SemgrepRunError(RuntimeError):
    """Raised when a Semgrep scan cannot produce normalized output."""


def _semgrep_executable() -> str:
    executable_name = "semgrep.exe" if os.name == "nt" else "semgrep"
    installed_executable = Path(sys.executable).with_name(executable_name)
    if installed_executable.is_file():
        return installed_executable.as_posix()
    return "semgrep"


def _command_error(completed: subprocess.CompletedProcess[str]) -> SemgrepRunError:
    return SemgrepRunError(
        "Semgrep command failed with exit code "
        f"{completed.returncode}: inspect the local Semgrep error output."
    )


def run_scan(
    target: Path, artifacts: Path, *, excludes: Sequence[str] = ()
) -> Path:
    """Run Semgrep once and return the normalized findings artifact path."""
    artifacts.mkdir(parents=True, exist_ok=True)
    raw_output = artifacts / "semgrep-result.json"
    findings_output = artifacts / "findings.json"
    raw_output.unlink(missing_ok=True)
    findings_output.unlink(missing_ok=True)

    command = [
        _semgrep_executable(),
        "scan",
        "--config",
        RULESET,
        "--json",
    ]
    for exclusion in excludes:
        command.extend(("--exclude", exclusion))
    command.extend(("--output", raw_output.as_posix(), target.as_posix()))
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
            text=True,
        )
    except FileNotFoundError as error:
        raise SemgrepRunError(
            "Semgrep executable was not found. Install requirements-dev.txt first."
        ) from error

    if completed.returncode not in (0, 1):
        raise _command_error(completed)
    if not raw_output.is_file():
        raise SemgrepRunError("Semgrep did not create semgrep-result.json")

    try:
        payload = json.loads(raw_output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SemgrepRunError("semgrep-result.json is not valid JSON") from error

    try:
        document = normalize_semgrep(payload, payload.get("version", SEMGREP_VERSION), target.as_posix())
    except SemgrepFormatError as error:
        raise SemgrepRunError(str(error)) from error

    findings_output.write_text(
        json.dumps(document.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return findings_output


def main(argv: Sequence[str] | None = None) -> int:
    """Run a Semgrep scan from the command line."""
    parser = argparse.ArgumentParser(description="Run a local Semgrep security scan.")
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    parser.add_argument("--exclude", action="append", default=[])
    arguments = parser.parse_args(argv)
    try:
        result = run_scan(arguments.target, arguments.artifacts, excludes=arguments.exclude)
    except SemgrepRunError as error:
        print(error, file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
