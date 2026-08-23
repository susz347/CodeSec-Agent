"""Run Bandit and write local scan artifacts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from scanner.normalize_bandit import BanditFormatError, normalize_bandit


BANDIT_VERSION = "1.9.4"


class BanditRunError(RuntimeError):
    """Raised when Bandit cannot produce normalized output."""


def _bandit_executable() -> str:
    name = "bandit.exe" if os.name == "nt" else "bandit"
    installed = Path(sys.executable).with_name(name)
    return installed.as_posix() if installed.is_file() else "bandit"


def run_scan(target: Path, artifacts: Path) -> Path:
    artifacts.mkdir(parents=True, exist_ok=True)
    raw = artifacts / "bandit-result.json"
    findings = artifacts / "bandit-findings.json"
    raw.unlink(missing_ok=True)
    findings.unlink(missing_ok=True)
    command = [_bandit_executable(), "-r", target.as_posix(), "-f", "json", "-o", raw.as_posix()]
    try:
        result = subprocess.run(command, capture_output=True, check=False, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError as error:
        raise BanditRunError("Bandit executable was not found. Install requirements-dev.txt first.") from error
    if result.returncode not in (0, 1):
        raise BanditRunError(f"Bandit command failed with exit code {result.returncode}.")
    if not raw.is_file():
        raise BanditRunError("Bandit did not create bandit-result.json")
    try:
        payload = json.loads(raw.read_text(encoding="utf-8"))
        document = normalize_bandit(payload, BANDIT_VERSION, target.as_posix())
    except (OSError, json.JSONDecodeError, BanditFormatError) as error:
        raise BanditRunError(f"bandit-result.json could not be normalized: {error}") from error
    findings.write_text(json.dumps(document.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local Bandit security scan.")
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    arguments = parser.parse_args(argv)
    try:
        print(run_scan(arguments.target, arguments.artifacts))
    except BanditRunError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
