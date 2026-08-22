import json
import tempfile
import unittest
from pathlib import Path

from reporting.cli import main


class ReportingCliTests(unittest.TestCase):
    def test_writes_both_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "findings.json"; output = root / "reports"
            source.write_text(json.dumps({"schema_version":"1.0","scan":{"tool":"semgrep","tool_version":"1","ruleset":"rules","target":".","started_at":"2026-08-22T00:00:00Z"},"findings":[]}), encoding="utf-8")
            self.assertEqual(main(["--input", str(source), "--output-dir", str(output)]), 0)
            self.assertTrue((output / "security-report.json").is_file())
            self.assertTrue((output / "security-report.md").is_file())

    def test_invalid_input_leaves_no_partial_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "bad.json"; output = root / "reports"
            source.write_text("not json", encoding="utf-8")
            self.assertEqual(main(["--input", str(source), "--output-dir", str(output)]), 1)
            self.assertFalse((output / "security-report.json").exists())
            self.assertFalse((output / "security-report.md").exists())


if __name__ == "__main__": unittest.main()
