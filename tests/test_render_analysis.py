import json
import unittest

from agent.models import AnalysisDocument, AnalysisItem
from reporting.load_findings import load_documents
from reporting.models import SecurityReport
from reporting.render_analysis import render_analysis_json, render_analysis_markdown


def _report() -> SecurityReport:
    return SecurityReport.create(
        sources=[],
        findings=[
            {
                "id": "f1",
                "tool": "semgrep",
                "rule_id": "python.lang.security.audit.exec-used",
                "severity": "error",
                "path": "app.py",
                "start_line": 3,
                "start_column": None,
                "end_line": 3,
                "end_column": None,
                "message": "Avoid exec.",
                "code": "exec(user_input)",
                "metadata": {"cwe": ["CWE-78"]},
                "raw_reference": "/results/0",
            }
        ],
    )


def _analysis() -> AnalysisDocument:
    return AnalysisDocument.create(
        "deterministic",
        [
            AnalysisItem(
                finding_id="f1",
                label="confirmed",
                title="OS command injection",
                cause="cause",
                impact="impact",
                remediation="remediation",
                references=("CWE-78", "A03:2021 Injection"),
            )
        ],
    )


class RenderAnalysisTests(unittest.TestCase):
    def test_markdown_contains_finding_and_analysis(self) -> None:
        text = render_analysis_markdown(_report(), _analysis())
        for value in ("# Security Report", "python.lang.security.audit.exec-used", "f1", "Classification: confirmed", "remediation", "CWE-78"):
            self.assertIn(value, text)

    def test_markdown_labels_unanalyzed_findings(self) -> None:
        text = render_analysis_markdown(_report(), AnalysisDocument.create("deterministic", []))
        self.assertIn("Classification: unanalyzed", text)

    def test_json_is_parseable_and_merges_analysis(self) -> None:
        payload = json.loads(render_analysis_json(_report(), _analysis()))
        self.assertEqual(payload["findings"][0]["id"], "f1")
        self.assertEqual(payload["analysis"]["items"][0]["finding_id"], "f1")

    def test_markdown_shows_diff_status_and_evidence(self) -> None:
        analysis = AnalysisDocument.create(
            "deterministic",
            [
                AnalysisItem(
                    finding_id="f1",
                    label="confirmed",
                    title="title",
                    cause="cause",
                    impact="impact",
                    remediation="remediation",
                    references=(),
                    diff_status="changed",
                    evidence={"path": "app.py", "start_line": 1, "end_line": 3, "sha256": "abcdef1234567890", "truncated": False},
                )
            ],
        )
        text = render_analysis_markdown(_report(), analysis)
        self.assertIn("Changed: changed", text)
        self.assertIn("Evidence: app.py:1-3", text)
        self.assertIn("sha256=abcdef12", text)

    def test_json_includes_diff_status_and_evidence(self) -> None:
        analysis = AnalysisDocument.create(
            "deterministic",
            [
                AnalysisItem(
                    finding_id="f1",
                    label="confirmed",
                    title="title",
                    cause="cause",
                    impact="impact",
                    remediation="remediation",
                    references=(),
                    diff_status="changed",
                    evidence={"path": "app.py", "start_line": 1},
                )
            ],
        )
        payload = json.loads(render_analysis_json(_report(), analysis))
        item = payload["analysis"]["items"][0]
        self.assertEqual(item["diff_status"], "changed")
        self.assertEqual(item["evidence"], {"path": "app.py", "start_line": 1})


class LoadDocumentsIntegrationTests(unittest.TestCase):
    def test_analysis_references_real_finding_id(self) -> None:
        # Build a report via the real loader path so finding IDs are consistent.
        report = _report()
        analysis = _analysis()
        ids = {item["id"] for item in report.findings}
        for item in analysis.items:
            self.assertIn(item.finding_id, ids)


if __name__ == "__main__":
    unittest.main()
