import unittest
from io import BytesIO

from pypdf import PdfReader

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


if __name__ == "__main__":
    unittest.main()
