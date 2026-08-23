import unittest

from reporting.risk import DIFF_ORDER, LABEL_ORDER, order_findings, risk_key


def finding(identifier: str, severity: str = "error", path: str = "a.py") -> dict[str, object]:
    return {
        "id": identifier,
        "tool": "semgrep",
        "rule_id": "rule",
        "severity": severity,
        "path": path,
        "start_line": 1,
        "message": "message",
        "code": None,
        "metadata": {},
        "raw_reference": "/results/0",
    }


def item(label: str, diff_status: str) -> dict[str, object]:
    return {"label": label, "diff_status": diff_status}


class RiskOrderingTests(unittest.TestCase):
    def test_label_ranks_confirmed_first(self) -> None:
        findings = [
            finding("fp"),
            finding("suspicious"),
            finding("confirmed"),
        ]
        items = {
            "fp": item("possible_false_positive", "changed"),
            "suspicious": item("suspicious", "changed"),
            "confirmed": item("confirmed", "changed"),
        }
        ordered = order_findings(findings, items)
        self.assertEqual(
            [f["id"] for f in ordered], ["confirmed", "suspicious", "fp"]
        )

    def test_diff_ranks_changed_before_unchanged(self) -> None:
        findings = [finding("unchanged"), finding("changed")]
        items = {
            "unchanged": item("confirmed", "unchanged"),
            "changed": item("confirmed", "changed"),
        }
        ordered = order_findings(findings, items)
        self.assertEqual([f["id"] for f in ordered], ["changed", "unchanged"])

    def test_severity_breaks_label_and_diff_ties(self) -> None:
        findings = [finding("info", "info"), finding("error", "error")]
        items = {
            "info": item("confirmed", "changed"),
            "error": item("confirmed", "changed"),
        }
        ordered = order_findings(findings, items)
        self.assertEqual([f["id"] for f in ordered], ["error", "info"])

    def test_unanalyzed_finding_sorts_last(self) -> None:
        findings = [finding("plain"), finding("analyzed")]
        items = {"analyzed": item("confirmed", "changed")}
        ordered = order_findings(findings, items)
        self.assertEqual([f["id"] for f in ordered], ["analyzed", "plain"])

    def test_no_analysis_degrades_to_severity_order(self) -> None:
        findings = [finding("info", "info"), finding("error", "error")]
        ordered = order_findings(findings, {})
        self.assertEqual([f["id"] for f in ordered], ["error", "info"])

    def test_risk_key_orders_are_stable(self) -> None:
        self.assertLess(LABEL_ORDER["confirmed"], LABEL_ORDER["possible_false_positive"])
        self.assertLess(DIFF_ORDER["changed"], DIFF_ORDER["unchanged"])
        self.assertLess(
            risk_key(finding("a"), item("confirmed", "changed"))[0],
            risk_key(finding("b"), item("suspicious", "changed"))[0],
        )


if __name__ == "__main__":
    unittest.main()
