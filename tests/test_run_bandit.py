import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scanner.run_bandit import BanditRunError, run_scan


PAYLOAD = {"errors": [], "results": []}


class RunBanditTests(unittest.TestCase):
    def test_finding_exit_code_writes_normalized_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifacts = Path(directory) / "artifacts"

            def write_raw(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                Path(command[-1]).write_text(json.dumps(PAYLOAD), encoding="utf-8")
                return subprocess.CompletedProcess(command, 1, "", "")

            with patch("scanner.run_bandit.subprocess.run", side_effect=write_raw) as run:
                result = run_scan(Path("."), artifacts)

            self.assertEqual(result, artifacts / "bandit-findings.json")
            self.assertEqual(json.loads(result.read_text(encoding="utf-8"))["findings"], [])
            self.assertEqual(run.call_args.args[0][1:], ["-r", ".", "-f", "json", "-o", (artifacts / "bandit-result.json").as_posix()])

    def test_unexpected_exit_code_and_missing_output_raise(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifacts = Path(directory) / "artifacts"
            with patch("scanner.run_bandit.subprocess.run", return_value=subprocess.CompletedProcess([], 2, "", "")):
                with self.assertRaises(BanditRunError):
                    run_scan(Path("."), artifacts)
            with patch("scanner.run_bandit.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", "")):
                with self.assertRaises(BanditRunError):
                    run_scan(Path("."), artifacts)


if __name__ == "__main__":
    unittest.main()
