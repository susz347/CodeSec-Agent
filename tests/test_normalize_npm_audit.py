import json
import unittest
from pathlib import Path

from scanner.normalize_npm_audit import NpmAuditFormatError, normalize_npm_audit


FIXTURES = Path(__file__).parent / "fixtures" / "npm-audit"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class NormalizeNpmAuditTests(unittest.TestCase):
    def test_empty_vulnerabilities_remain_empty(self) -> None:
        self.assertEqual(normalize_npm_audit(load_fixture("empty.json"), "10", ".").to_dict()["findings"], [])

    def test_complete_vulnerability_maps_to_finding(self) -> None:
        finding = normalize_npm_audit(load_fixture("findings.json"), "10", ".").to_dict()["findings"][0]
        self.assertEqual(finding["rule_id"], "npm-audit/lodash")
        self.assertEqual(finding["severity"], "error")
        self.assertEqual(finding["path"], "package-lock.json")
        self.assertEqual(finding["metadata"]["category"], "dependency")
        self.assertEqual(finding["metadata"]["cwe"], ["CWE-1321"])

    def test_missing_metadata_is_rejected(self) -> None:
        payload = load_fixture("empty.json")
        del payload["metadata"]
        with self.assertRaisesRegex(NpmAuditFormatError, r"/metadata"):
            normalize_npm_audit(payload, "10", ".")


if __name__ == "__main__":
    unittest.main()
