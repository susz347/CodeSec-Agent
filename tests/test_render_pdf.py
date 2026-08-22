import unittest
from io import BytesIO

from pypdf import PdfReader

from agent.models import AnalysisDocument, AnalysisItem
from reporting.models import ScanSource, SecurityReport
from reporting.render_pdf import render_pdf


class PdfRendererTests(unittest.TestCase):
    def test_pdf_contains_report_sections(self) -> None:
        source = ScanSource("semgrep", "1", "rules", ".", "2026-08-22T00:00:00Z")
        finding = {
            "id": "id",
            "tool": "semgrep",
            "rule_id": "rule",
            "severity": "error",
            "path": "a.py",
            "start_line": 2,
            "message": "Avoid exec.",
            "code": "exec(x)",
            "metadata": {"cwe": ["CWE-78"]},
            "raw_reference": "/results/0",
        }
        report = SecurityReport.create([source], [finding])

        reader = PdfReader(BytesIO(render_pdf(report)))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        self.assertGreaterEqual(len(reader.pages), 1)
        for value in ("Security Report", "Scan Sources", "Summary", "Avoid exec."):
            self.assertIn(value, text)

    def test_pdf_renders_analysis_fields(self) -> None:
        source = ScanSource("semgrep", "1", "rules", ".", "2026-08-22T00:00:00Z")
        finding = {
            "id": "id",
            "tool": "semgrep",
            "rule_id": "rule",
            "severity": "error",
            "path": "a.py",
            "start_line": 2,
            "message": "Avoid exec.",
            "code": "exec(x)",
            "metadata": {},
            "raw_reference": "/results/0",
        }
        report = SecurityReport.create([source], [finding])
        analysis = AnalysisDocument.create(
            "deterministic",
            [
                AnalysisItem(
                    "id", "confirmed", "title", "cause", "impact", "remediation",
                    ("CWE-78",), diff_status="changed",
                )
            ],
        )

        reader = PdfReader(BytesIO(render_pdf(report, analysis)))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        for value in ("Classification: confirmed", "Changed: changed", "Cause: cause", "CWE-78"):
            self.assertIn(value, text)


if __name__ == "__main__":
    unittest.main()
