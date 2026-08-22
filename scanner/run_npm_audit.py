"""Run npm audit without installing or modifying dependencies."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from scanner.normalize_npm_audit import NpmAuditFormatError, normalize_npm_audit


class NpmAuditNotApplicable(RuntimeError):
    """Raised when a target does not contain an npm lockfile."""


class NpmAuditRunError(RuntimeError):
    """Raised when npm audit cannot produce normalized output."""


def _npm_executable() -> str:
    return os.environ.get("NPM_EXECUTABLE", "npm")


def run_scan(target: Path, artifacts: Path) -> Path:
    if not (target / "package-lock.json").is_file():
        raise NpmAuditNotApplicable("npm audit requires a target-local package-lock.json")
    artifacts.mkdir(parents=True, exist_ok=True)
    raw, findings = artifacts / "npm-audit-result.json", artifacts / "npm-audit-findings.json"
    raw.unlink(missing_ok=True); findings.unlink(missing_ok=True)
    try:
        npm = _npm_executable()
        version = subprocess.run([npm, "--version"], capture_output=True, check=False, text=True, encoding="utf-8", errors="replace")
        result = subprocess.run([npm, "audit", "--json", "--package-lock-only", "--ignore-scripts"], cwd=target, capture_output=True, check=False, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError as error:
        raise NpmAuditRunError("npm executable was not found.") from error
    if version.returncode != 0 or not version.stdout.strip(): raise NpmAuditRunError("npm --version failed.")
    if result.returncode not in (0, 1): raise NpmAuditRunError(f"npm audit failed with exit code {result.returncode}.")
    try:
        payload = json.loads(result.stdout)
        document = normalize_npm_audit(payload, version.stdout.strip(), target.as_posix())
    except (json.JSONDecodeError, NpmAuditFormatError) as error:
        raise NpmAuditRunError("npm audit did not produce valid JSON.") from error
    raw.write_text(result.stdout, encoding="utf-8")
    findings.write_text(json.dumps(document.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run npm audit safely.")
    parser.add_argument("--target", type=Path, default=Path(".")); parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    arguments = parser.parse_args(argv)
    try: print(run_scan(arguments.target, arguments.artifacts))
    except (NpmAuditNotApplicable, NpmAuditRunError) as error:
        print(error, file=sys.stderr); return 1
    return 0


if __name__ == "__main__": raise SystemExit(main())
