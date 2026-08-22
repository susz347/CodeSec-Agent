import unittest

from agent.models import AnalysisFormatError, LABELS
from agent.security_reviewer import DeterministicReviewer, LlmReviewer, analyze


def finding(
    identifier: str = "f1",
    severity: str = "error",
    rule_id: str = "python.lang.security.audit.exec-used",
    tool: str = "semgrep",
    path: str = "app.py",
    code: str | None = "exec(user_input)",
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "id": identifier,
        "tool": tool,
        "rule_id": rule_id,
        "severity": severity,
        "path": path,
        "start_line": 3,
        "start_column": None,
        "end_line": 3,
        "end_column": None,
        "message": "Avoid exec.",
        "code": code,
        "metadata": metadata or {},
        "raw_reference": "/results/0",
    }


class DeterministicReviewerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reviewer = DeterministicReviewer()

    def test_analyzes_each_finding(self) -> None:
        document = self.reviewer.analyze([finding("a"), finding("b")])
        self.assertEqual([item.finding_id for item in document.items], ["a", "b"])

    def test_labels_are_valid(self) -> None:
        document = self.reviewer.analyze(
            [finding(severity="warning"), finding(severity="info"), finding(severity="unknown")]
        )
        for item in document.items:
            self.assertIn(item.label, LABELS)

    def test_error_is_confirmed(self) -> None:
        item = self.reviewer.analyze([finding(severity="error")]).items[0]
        self.assertEqual(item.label, "confirmed")

    def test_warning_is_suspicious(self) -> None:
        item = self.reviewer.analyze(
            [finding(severity="warning", rule_id="some.rule", code="x = 1")]
        ).items[0]
        self.assertEqual(item.label, "suspicious")

    def test_info_is_possible_false_positive(self) -> None:
        item = self.reviewer.analyze(
            [finding(severity="info", rule_id="some.rule")]
        ).items[0]
        self.assertEqual(item.label, "possible_false_positive")

    def test_test_path_downgrades(self) -> None:
        item = self.reviewer.analyze(
            [finding(severity="error", path="tests/test_app.py")]
        ).items[0]
        self.assertEqual(item.label, "suspicious")

    def test_missing_code_downgrades_error(self) -> None:
        item = self.reviewer.analyze([finding(severity="error", code=None)]).items[0]
        self.assertEqual(item.label, "suspicious")

    def test_high_confidence_confirms_with_code(self) -> None:
        item = self.reviewer.analyze(
            [finding(severity="warning", rule_id="python.lang.security.audit.exec-used", code="exec(x)")]
        ).items[0]
        self.assertEqual(item.label, "confirmed")

    def test_commented_code_is_possible_false_positive(self) -> None:
        item = self.reviewer.analyze(
            [finding(severity="error", code="# exec(user_input)")]
        ).items[0]
        self.assertEqual(item.label, "possible_false_positive")

    def test_npm_audit_high_is_confirmed(self) -> None:
        item = self.reviewer.analyze(
            [
                finding(
                    identifier="n",
                    tool="npm-audit",
                    severity="error",
                    rule_id="npm-audit/lodash",
                    code=None,
                    path="package-lock.json",
                )
            ]
        ).items[0]
        self.assertEqual(item.label, "confirmed")

    def test_analysis_is_deterministic(self) -> None:
        first = self.reviewer.analyze([finding()])
        second = self.reviewer.analyze([finding()])
        self.assertEqual(
            [item.to_dict() for item in first.items],
            [item.to_dict() for item in second.items],
        )

    def test_defaults_diff_status_and_evidence(self) -> None:
        item = self.reviewer.analyze([finding()]).items[0]
        self.assertEqual(item.diff_status, "unknown")
        self.assertIsNone(item.evidence)

    def test_passes_diff_status_and_evidence(self) -> None:
        document = self.reviewer.analyze(
            [finding("a")],
            diff_statuses={"a": "changed"},
            evidence={"a": {"path": "app.py"}},
        )
        item = document.items[0]
        self.assertEqual(item.diff_status, "changed")
        self.assertEqual(item.evidence, {"path": "app.py"})


class AnalyzeEntrypointTests(unittest.TestCase):
    def test_analyze_requires_findings_array(self) -> None:
        with self.assertRaises(AnalysisFormatError):
            analyze({"schema_version": "1.0"})

    def test_analyze_skips_non_dict_findings(self) -> None:
        document = analyze({"schema_version": "1.0", "findings": [finding(), "junk"]})
        self.assertEqual(len(document.items), 1)

    def test_analyze_forwards_diff_status_and_evidence(self) -> None:
        document = analyze(
            {"schema_version": "1.0", "findings": [finding("a")]},
            diff_statuses={"a": "unchanged"},
            evidence={"a": {"path": "app.py", "start_line": 3}},
        )
        item = document.items[0]
        self.assertEqual(item.diff_status, "unchanged")
        self.assertEqual(item.evidence, {"path": "app.py", "start_line": 3})


class LlmReviewerTests(unittest.TestCase):
    def test_llm_reviewer_is_not_implemented(self) -> None:
        with self.assertRaises(NotImplementedError):
            LlmReviewer().analyze([])


if __name__ == "__main__":
    unittest.main()
