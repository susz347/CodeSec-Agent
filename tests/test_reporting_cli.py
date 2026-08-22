import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from reporting.cli import main


class ReportingCliTests(unittest.TestCase):
    def test_writes_both_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "findings.json"; output = root / "reports"
            source.write_text(json.dumps({"schema_version":"1.0","scan":{"tool":"semgrep","tool_version":"1","ruleset":"rules","target":".","started_at":"2026-08-22T00:00:00Z"},"findings":[]}), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                result = main(["--input", str(source), "--output-dir", str(output)])
            self.assertEqual(result, 0)
            self.assertTrue((output / "security-report.json").is_file())
            self.assertTrue((output / "security-report.md").is_file())

    def test_invalid_input_leaves_no_partial_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "bad.json"; output = root / "reports"
            source.write_text("not json", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                result = main(["--input", str(source), "--output-dir", str(output)])
            self.assertEqual(result, 1)
            self.assertFalse((output / "security-report.json").exists())
            self.assertFalse((output / "security-report.md").exists())

    def test_write_failure_restores_both_previous_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "findings.json"; output = root / "reports"
            source.write_text(json.dumps({"schema_version":"1.0","scan":{"tool":"semgrep","tool_version":"1","ruleset":"rules","target":".","started_at":"2026-08-22T00:00:00Z"},"findings":[]}), encoding="utf-8")
            output.mkdir()
            json_output = output / "security-report.json"
            markdown_output = output / "security-report.md"
            json_output.write_text("old json", encoding="utf-8")
            markdown_output.write_text("old markdown", encoding="utf-8")
            original_replace = Path.replace

            def fail_markdown_commit(path: Path, target: Path) -> Path:
                if path.name == ".security-report.md.tmp":
                    raise OSError("simulated write failure")
                return original_replace(path, target)

            with patch("reporting.cli.Path.replace", autospec=True, side_effect=fail_markdown_commit):
                with redirect_stderr(io.StringIO()):
                    result = main(["--input", str(source), "--output-dir", str(output)])

            self.assertEqual(result, 1)
            self.assertEqual(json_output.read_text(encoding="utf-8"), "old json")
            self.assertEqual(markdown_output.read_text(encoding="utf-8"), "old markdown")


if __name__ == "__main__": unittest.main()
