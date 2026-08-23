import unittest

from reporting.summary import render_pr_summary


def _payload() -> dict[str, object]:
    return {
        "counts": {"error": 1, "warning": 2, "info": 0, "unknown": 0},
        "findings": [
            {"rule_id": "B101", "path": "example.py", "code": "assert value"},
            {"rule_id": "npm-audit/lodash", "path": "package-lock.json", "code": None},
        ],
        "analysis": {
            "items": [
                {"finding_id": "a", "label": "confirmed"},
                {"finding_id": "b", "label": "suspicious"},
            ]
        },
    }


class RenderPrSummaryTests(unittest.TestCase):
    def test_includes_counts_and_classification(self) -> None:
        text = render_pr_summary(_payload())
        self.assertIn("Total findings: 2", text)
        self.assertIn("error=1", text)
        self.assertIn("confirmed=1", text)
        self.assertIn("suspicious=1", text)

    def test_includes_rule_ids_and_paths(self) -> None:
        text = render_pr_summary(_payload())
        self.assertIn("`B101`", text)
        self.assertIn("`example.py`", text)

    def test_never_includes_source_code(self) -> None:
        text = render_pr_summary(_payload())
        self.assertNotIn("assert value", text)

    def test_high_severity_adds_review_warning(self) -> None:
        text = render_pr_summary(_payload())
        self.assertIn("recommend human review", text)

    def test_no_high_severity_omits_warning(self) -> None:
        payload = _payload()
        payload["counts"] = {"error": 0, "warning": 0, "info": 0, "unknown": 0}
        text = render_pr_summary(payload)
        self.assertNotIn("recommend human review", text)

    def test_includes_artifacts_url_when_provided(self) -> None:
        text = render_pr_summary(_payload(), artifacts_url="https://example/run")
        self.assertIn("https://example/run", text)

    def test_includes_diff_counts_when_changed_present(self) -> None:
        payload = _payload()
        payload["analysis"]["items"] = [
            {"finding_id": "a", "label": "confirmed", "diff_status": "changed"},
            {"finding_id": "b", "label": "suspicious", "diff_status": "unchanged"},
        ]
        text = render_pr_summary(payload)
        self.assertIn("changed=1", text)
        self.assertIn("unchanged=1", text)

    def test_omits_diff_line_when_all_unknown(self) -> None:
        text = render_pr_summary(_payload())
        self.assertNotIn("- Diff:", text)

    def test_focuses_rules_and_paths_on_new_baseline_findings(self) -> None:
        payload = _payload()
        payload["findings"] = [
            {"id": "a", "rule_id": "NEW-RULE", "path": "new.py"},
            {"id": "b", "rule_id": "OLD-RULE", "path": "old.py"},
        ]
        payload["analysis"]["items"] = [
            {"finding_id": "a", "label": "confirmed", "baseline_status": "new"},
            {"finding_id": "b", "label": "suspicious", "baseline_status": "existing"},
        ]
        text = render_pr_summary(payload)
        self.assertIn("Baseline: new=1, existing=1, unknown=0", text)
        self.assertIn("`NEW-RULE`", text)
        self.assertNotIn("`OLD-RULE`", text)

    def test_baseline_does_not_warn_for_existing_high_severity_finding(self) -> None:
        payload = _payload()
        payload["findings"] = [{"id": "a", "rule_id": "OLD-RULE", "path": "old.py", "severity": "error"}]
        payload["analysis"]["items"] = [
            {"finding_id": "a", "label": "confirmed", "baseline_status": "existing"}
        ]
        text = render_pr_summary(payload)
        self.assertNotIn("recommend human review", text)


if __name__ == "__main__":
    unittest.main()
