import io
import json
import sys
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
            self.assertEqual(len(list(output.glob("security-report.*"))), 2)

    def test_writes_manifest_alongside_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "findings.json"; output = root / "reports"
            source.write_text(json.dumps({"schema_version":"1.0","scan":{"tool":"semgrep","tool_version":"1","ruleset":"rules","target":".","started_at":"2026-08-22T00:00:00Z"},"findings":[]}), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                result = main(["--input", str(source), "--output-dir", str(output)])
            self.assertEqual(result, 0)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                {artifact["path"] for artifact in manifest["artifacts"]},
                {"security-report.json", "security-report.md"},
            )

    def test_analysis_enriches_markdown_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "findings.json"; output = root / "reports"
            finding = {
                "id": "f1", "tool": "semgrep", "rule_id": "python.lang.security.audit.exec-used",
                "severity": "error", "path": "app.py", "start_line": 3, "start_column": None,
                "end_line": 3, "end_column": None, "message": "Avoid exec.",
                "code": "exec(user_input)", "metadata": {}, "raw_reference": "/results/0",
            }
            source.write_text(json.dumps({"schema_version": "1.0", "scan": {"tool": "semgrep", "tool_version": "1", "ruleset": "rules", "target": ".", "started_at": "2026-08-22T00:00:00Z"}, "findings": [finding]}), encoding="utf-8")
            analysis_path = root / "analysis.json"
            analysis_path.write_text(json.dumps({"schema_version": "1.0", "backend": "deterministic", "generated_at": "2026-08-22T00:00:00Z", "items": [{"finding_id": "f1", "label": "confirmed", "title": "t", "cause": "c", "impact": "i", "remediation": "r", "references": ["CWE-78"]}]}), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                result = main(["--input", str(source), "--output-dir", str(output), "--analysis", str(analysis_path)])
            self.assertEqual(result, 0)
            markdown = (output / "security-report.md").read_text(encoding="utf-8")
            self.assertIn("Classification: confirmed", markdown)
            self.assertIn("Remediation: r", markdown)

    def test_invalid_analysis_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "findings.json"; output = root / "reports"
            source.write_text(json.dumps({"schema_version":"1.0","scan":{"tool":"semgrep","tool_version":"1","ruleset":"rules","target":".","started_at":"2026-08-22T00:00:00Z"},"findings":[]}), encoding="utf-8")
            analysis_path = root / "analysis.json"
            analysis_path.write_text('{"schema_version":"2.0","items":[]}', encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                result = main(["--input", str(source), "--output-dir", str(output), "--analysis", str(analysis_path)])
            self.assertEqual(result, 1)
            self.assertFalse((output / "security-report.md").exists())

    def test_all_format_generates_five_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "findings.json"; output = root / "reports"
            source.write_text(json.dumps({"schema_version":"1.0","scan":{"tool":"semgrep","tool_version":"1","ruleset":"rules","target":".","started_at":"2026-08-22T00:00:00Z"},"findings":[]}), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                result = main(["--input", str(source), "--output-dir", str(output), "--format", "all"])
            self.assertEqual(result, 0)
            self.assertEqual(
                {path.suffix for path in output.glob("security-report.*")},
                {".json", ".md", ".xlsx", ".docx", ".pdf"},
            )

    def test_invalid_input_leaves_no_partial_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "bad.json"; output = root / "reports"
            source.write_text("not json", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                result = main(["--input", str(source), "--output-dir", str(output)])
            self.assertEqual(result, 1)
            self.assertFalse((output / "security-report.json").exists())
            self.assertFalse((output / "security-report.md").exists())

    def test_write_failure_restores_all_previous_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "findings.json"; output = root / "reports"
            source.write_text(json.dumps({"schema_version":"1.0","scan":{"tool":"semgrep","tool_version":"1","ruleset":"rules","target":".","started_at":"2026-08-22T00:00:00Z"},"findings":[]}), encoding="utf-8")
            output.mkdir()
            previous = {
                output / f"security-report.{extension}": f"old {extension}".encode()
                for extension in ("json", "md", "xlsx", "docx", "pdf")
            }
            for path, content in previous.items():
                path.write_bytes(content)
            original_replace = Path.replace

            def fail_pdf_commit(path: Path, target: Path) -> Path:
                if path.name == ".security-report.pdf.tmp":
                    raise OSError("simulated write failure")
                return original_replace(path, target)

            with patch("reporting.cli.Path.replace", autospec=True, side_effect=fail_pdf_commit):
                with redirect_stderr(io.StringIO()):
                    result = main(["--input", str(source), "--output-dir", str(output), "--format", "all"])

            self.assertEqual(result, 1)
            for path, content in previous.items():
                self.assertEqual(path.read_bytes(), content)

    def test_partial_temporary_write_is_cleaned_up(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "findings.json"; output = root / "reports"
            source.write_text(json.dumps({"schema_version":"1.0","scan":{"tool":"semgrep","tool_version":"1","ruleset":"rules","target":".","started_at":"2026-08-22T00:00:00Z"},"findings":[]}), encoding="utf-8")
            original_write_bytes = Path.write_bytes

            def fail_pdf_write(path: Path, content: bytes) -> int:
                if path.name == ".security-report.pdf.tmp":
                    original_write_bytes(path, b"partial")
                    raise OSError("simulated temporary write failure")
                return original_write_bytes(path, content)

            with patch("reporting.cli.Path.write_bytes", autospec=True, side_effect=fail_pdf_write):
                with redirect_stderr(io.StringIO()):
                    result = main(["--input", str(source), "--output-dir", str(output), "--format", "all"])

            self.assertEqual(result, 1)
            self.assertEqual(list(output.glob(".*.tmp")), [])

    def test_missing_optional_dependency_returns_install_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "findings.json"; output = root / "reports"
            source.write_text(json.dumps({"schema_version":"1.0","scan":{"tool":"semgrep","tool_version":"1","ruleset":"rules","target":".","started_at":"2026-08-22T00:00:00Z"},"findings":[]}), encoding="utf-8")
            stderr = io.StringIO()

            with patch.dict(sys.modules, {"reporting.render_excel": None}):
                with redirect_stderr(stderr):
                    result = main(["--input", str(source), "--output-dir", str(output), "--format", "xlsx"])

            self.assertEqual(result, 1)
            self.assertIn("pip install -r requirements-dev.txt", stderr.getvalue())
            self.assertFalse(output.exists())


if __name__ == "__main__": unittest.main()
