import json
import unittest
from pathlib import Path

from scanner.normalize_semgrep import SemgrepFormatError, normalize_semgrep


FIXTURES = Path(__file__).parent / "fixtures" / "semgrep"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class NormalizeSemgrepTests(unittest.TestCase):
    def test_empty_results_remain_empty(self) -> None:
        document = normalize_semgrep(load_fixture("empty.json"), "1.163.0", ".")
        self.assertEqual(document.to_dict()["findings"], [])

    def test_complete_result_maps_stable_fields(self) -> None:
        document = normalize_semgrep(load_fixture("findings.json"), "1.163.0", ".")
        finding = document.to_dict()["findings"][0]
        self.assertEqual(finding["rule_id"], "python.lang.security.audit.exec-used")
        self.assertEqual(finding["path"], "example.py")
        self.assertEqual(finding["start_line"], 3)
        self.assertEqual(finding["metadata"]["cwe"], ["CWE-78"])
        self.assertEqual(finding["raw_reference"], "/results/0")

    def test_missing_top_level_paths_is_rejected(self) -> None:
        with self.assertRaisesRegex(SemgrepFormatError, r"/paths"):
            normalize_semgrep(load_fixture("missing-required-field.json"), "1.163.0", ".")

    def test_missing_message_is_rejected_with_result_pointer(self) -> None:
        payload = load_fixture("missing-required-field.json")
        payload["paths"] = {"scanned": [], "skipped": []}
        with self.assertRaisesRegex(SemgrepFormatError, r"/results/0/extra/message"):
            normalize_semgrep(payload, "1.163.0", ".")


if __name__ == "__main__":
    unittest.main()
