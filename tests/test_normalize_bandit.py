import json
import unittest
from pathlib import Path

from scanner.normalize_bandit import BanditFormatError, normalize_bandit


FIXTURES = Path(__file__).parent / "fixtures" / "bandit"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class NormalizeBanditTests(unittest.TestCase):
    def test_empty_results_remain_empty(self) -> None:
        document = normalize_bandit(load_fixture("empty.json"), "1.9.4", ".")
        self.assertEqual(document.to_dict()["findings"], [])

    def test_complete_result_maps_to_normalized_finding(self) -> None:
        finding = normalize_bandit(
            load_fixture("findings.json"), "1.9.4", "."
        ).to_dict()["findings"][0]
        self.assertEqual(finding["tool"], "bandit")
        self.assertEqual(finding["rule_id"], "B101")
        self.assertEqual(finding["severity"], "warning")
        self.assertEqual(finding["path"], "example.py")
        self.assertEqual(finding["code"], "1 assert value\n")
        self.assertEqual(finding["metadata"]["references"], [
            "https://bandit.readthedocs.io/en/latest/plugins/b101_assert_used.html"
        ])
        self.assertEqual(finding["raw_reference"], "/results/0")

    def test_missing_errors_is_rejected(self) -> None:
        payload = load_fixture("empty.json")
        del payload["errors"]
        with self.assertRaisesRegex(BanditFormatError, r"/errors"):
            normalize_bandit(payload, "1.9.4", ".")

    def test_missing_issue_text_is_rejected_with_result_pointer(self) -> None:
        with self.assertRaisesRegex(BanditFormatError, r"/results/0/issue_text"):
            normalize_bandit(load_fixture("missing-field.json"), "1.9.4", ".")


if __name__ == "__main__":
    unittest.main()
