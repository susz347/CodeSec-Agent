import json
import unittest

from reporting.models import ScanSource, SecurityReport
from reporting.render_json import render_json
from reporting.render_markdown import render_markdown


class ReportRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        source = ScanSource("semgrep", "1", "rules", ".", "2026-08-22T00:00:00Z")
        finding = {"id":"id","tool":"semgrep","rule_id":"rule","severity":"error","path":"a.py","start_line":2,"start_column":1,"end_line":2,"end_column":2,"message":"Avoid exec.","code":"exec(x)","metadata":{"cwe":["CWE-78"]},"raw_reference":"/results/0"}
        self.report = SecurityReport.create([source], [finding])

    def test_json_contains_report_contract(self) -> None:
        payload = json.loads(render_json(self.report))
        self.assertEqual(payload["report_version"], "1.0")
        self.assertEqual(payload["summary"]["total"], 1)
        self.assertEqual(payload["findings"][0]["id"], "id")

    def test_markdown_contains_summary_and_finding(self) -> None:
        output = render_markdown(self.report)
        for text in ("# Security Report", "| error | 1 |", "a.py:2", "Avoid exec.", "exec(x)", "CWE-78"):
            self.assertIn(text, output)


if __name__ == "__main__": unittest.main()
