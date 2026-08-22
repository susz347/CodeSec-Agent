import unittest
from io import BytesIO
from zipfile import ZipFile

from reporting.models import ScanSource, SecurityReport
from reporting.render_docx import render_docx


class DocxRendererTests(unittest.TestCase):
    def test_docx_contains_report_sections(self) -> None:
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

        payload = render_docx(report)

        with ZipFile(BytesIO(payload)) as archive:
            document = archive.read("word/document.xml").decode("utf-8")
        for text in ("Security Report", "Scan Sources", "Summary", "rule", "Avoid exec."):
            self.assertIn(text, document)


if __name__ == "__main__":
    unittest.main()
