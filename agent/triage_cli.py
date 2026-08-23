"""Local commands for baseline and human-triage records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from agent.triage import TriageFormatError, add_disposition, build_baseline, load, save, statistics


def _findings(path: Path) -> list[dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TriageFormatError(f"Cannot read findings: {path}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        raise TriageFormatError("Unsupported finding schema")
    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise TriageFormatError("Missing findings array")
    return [item for item in findings if isinstance(item, dict)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage local security triage records.")
    commands = parser.add_subparsers(dest="command", required=True)
    baseline = commands.add_parser("baseline")
    baseline.add_argument("--input", required=True, type=Path)
    baseline.add_argument("--store", required=True, type=Path)
    disposition = commands.add_parser("disposition")
    disposition.add_argument("--store", required=True, type=Path)
    disposition.add_argument("--fingerprint", required=True)
    disposition.add_argument("--resolution", required=True, choices=("true_positive", "false_positive", "accepted_risk", "needs_fix"))
    disposition.add_argument("--reviewer", required=True)
    disposition.add_argument("--machine-label", required=True)
    disposition.add_argument("--note", default="")
    stats = commands.add_parser("stats")
    stats.add_argument("--store", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "baseline":
            save(arguments.store, build_baseline(_findings(arguments.input)))
        elif arguments.command == "disposition":
            save(arguments.store, add_disposition(load(arguments.store), fingerprint=arguments.fingerprint, resolution=arguments.resolution, reviewer=arguments.reviewer, machine_label=arguments.machine_label, note=arguments.note))
        else:
            print(json.dumps(statistics(load(arguments.store)), ensure_ascii=False, indent=2))
    except (TriageFormatError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
