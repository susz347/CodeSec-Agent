import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scanner.run_npm_audit import NpmAuditNotApplicable, NpmAuditRunError, run_scan


PAYLOAD = {"vulnerabilities": {}, "metadata": {"vulnerabilities": {"total": 0}}}


class RunNpmAuditTests(unittest.TestCase):
    def test_writes_audit_stdout_for_finding_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target, artifacts = Path(directory) / "target", Path(directory) / "artifacts"
            target.mkdir(); (target / "package-lock.json").write_text("{}", encoding="utf-8")
            calls = [subprocess.CompletedProcess([], 0, "10.0.0\n", ""), subprocess.CompletedProcess([], 1, json.dumps(PAYLOAD), "")]
            with patch("scanner.run_npm_audit.subprocess.run", side_effect=calls):
                result = run_scan(target, artifacts)
            self.assertEqual(result, artifacts / "npm-audit-findings.json")
            self.assertTrue((artifacts / "npm-audit-result.json").is_file())

    def test_missing_lockfile_and_bad_exit_raise(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target, artifacts = Path(directory) / "target", Path(directory) / "artifacts"
            target.mkdir()
            with self.assertRaises(NpmAuditNotApplicable): run_scan(target, artifacts)
            (target / "package-lock.json").write_text("{}", encoding="utf-8")
            calls = [subprocess.CompletedProcess([], 0, "10\n", ""), subprocess.CompletedProcess([], 2, "", "")]
            with patch("scanner.run_npm_audit.subprocess.run", side_effect=calls):
                with self.assertRaises(NpmAuditRunError): run_scan(target, artifacts)


if __name__ == "__main__":
    unittest.main()
