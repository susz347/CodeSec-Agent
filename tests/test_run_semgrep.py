import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scanner.run_semgrep import SemgrepRunError, run_scan


VALID_PAYLOAD = {"version": "1.163.0", "results": [], "errors": [], "paths": {}}


class RunSemgrepTests(unittest.TestCase):
    def test_accepts_finding_exit_code_and_writes_normalized_document(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifacts = Path(temporary_directory) / "artifacts"

            def write_raw_output(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                output = Path(command[command.index("--output") + 1])
                output.write_text(json.dumps(VALID_PAYLOAD), encoding="utf-8")
                return subprocess.CompletedProcess(command, 1, "", "")

            with patch("scanner.run_semgrep._semgrep_executable", return_value="semgrep"):
                with patch("scanner.run_semgrep.subprocess.run", side_effect=write_raw_output) as run:
                    result = run_scan(Path("."), artifacts)

            raw_output = artifacts / "semgrep-result.json"
            self.assertEqual(result, artifacts / "findings.json")
            self.assertEqual(json.loads(result.read_text(encoding="utf-8"))["findings"], [])
            run.assert_called_once_with(
                [
                    "semgrep",
                    "scan",
                    "--config",
                    "p/security-audit",
                    "--json",
                    "--output",
                    raw_output.as_posix(),
                    ".",
                ],
                capture_output=True,
                check=False,
                encoding="utf-8",
                errors="replace",
                text=True,
            )

    def test_unexpected_exit_code_raises_even_when_raw_output_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifacts = Path(temporary_directory) / "artifacts"

            def write_raw_output(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                output = Path(command[command.index("--output") + 1])
                output.write_text(json.dumps(VALID_PAYLOAD), encoding="utf-8")
                return subprocess.CompletedProcess(command, 2, "", "network failed")

            with patch("scanner.run_semgrep.subprocess.run", side_effect=write_raw_output):
                with self.assertRaises(SemgrepRunError):
                    run_scan(Path("."), artifacts)

            self.assertFalse((artifacts / "findings.json").exists())

    def test_missing_raw_output_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifacts = Path(temporary_directory) / "artifacts"
            completed = subprocess.CompletedProcess([], 0, "", "")
            with patch("scanner.run_semgrep.subprocess.run", return_value=completed):
                with self.assertRaises(SemgrepRunError):
                    run_scan(Path("."), artifacts)

    def test_prefers_semgrep_next_to_current_python(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            scripts = Path(temporary_directory) / "Scripts"
            scripts.mkdir()
            suffix = ".exe" if os.name == "nt" else ""
            python_executable = scripts / f"python{suffix}"
            semgrep_executable = scripts / f"semgrep{suffix}"
            python_executable.touch()
            semgrep_executable.touch()
            artifacts = Path(temporary_directory) / "artifacts"

            def write_raw_output(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                output = Path(command[command.index("--output") + 1])
                output.write_text(json.dumps(VALID_PAYLOAD), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch("scanner.run_semgrep.sys.executable", str(python_executable)):
                with patch("scanner.run_semgrep.subprocess.run", side_effect=write_raw_output) as run:
                    run_scan(Path("."), artifacts)

            self.assertEqual(run.call_args.args[0][0], semgrep_executable.as_posix())


if __name__ == "__main__":
    unittest.main()
