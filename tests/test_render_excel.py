import unittest
from io import BytesIO

from openpyxl import load_workbook

from reporting.models import ScanSource, SecurityReport
from reporting.render_excel import render_excel


class ExcelRendererTests(unittest.TestCase):
    def test_excel_contains_summary_sources_and_findings(self) -> None:
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

        workbook = load_workbook(BytesIO(render_excel(report)), data_only=False)

        self.assertEqual(workbook.sheetnames, ["Summary", "Sources", "Findings"])
        self.assertEqual(workbook["Summary"]["B3"].value, 1)
        self.assertTrue(workbook["Summary"]["A1"].font.bold)
        self.assertGreaterEqual(workbook["Summary"].row_dimensions[1].height or 0, 24)
        self.assertEqual(workbook["Sources"]["A2"].value, "semgrep")
        self.assertEqual(workbook["Findings"]["A2"].value, "id")
        self.assertEqual(workbook["Findings"]["G2"].value, "Avoid exec.")
        self.assertEqual(workbook["Sources"].page_setup.fitToWidth, 1)
        self.assertEqual(workbook["Findings"].page_setup.orientation, "landscape")


if __name__ == "__main__":
    unittest.main()
