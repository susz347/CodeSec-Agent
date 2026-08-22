import unittest

from scanner.models import Finding, ScanDocument


class FindingTests(unittest.TestCase):
    def test_unknown_severity_is_normalized_and_preserved(self) -> None:
        finding = Finding.create(
            rule_id="rule", severity="CRITICAL", path="example.py",
            start_line=3, start_column=1, end_line=3, end_column=16,
            message="Avoid exec.", code="exec(user_input)", metadata={},
            raw_reference="/results/0",
        )
        self.assertEqual(finding.severity, "unknown")
        self.assertEqual(finding.metadata["semgrep_severity"], "CRITICAL")

    def test_identifier_is_stable_for_the_same_location(self) -> None:
        arguments = {
            "rule_id": "rule", "severity": "warning", "path": "example.py",
            "start_line": 3, "start_column": 1, "end_line": 3,
            "end_column": 16, "message": "Avoid exec.",
            "code": "exec(user_input)", "metadata": {},
            "raw_reference": "/results/0",
        }
        self.assertEqual(Finding.create(**arguments).id, Finding.create(**arguments).id)

    def test_create_does_not_mutate_input_metadata(self) -> None:
        metadata = {"cwe": ["CWE-78"]}
        Finding.create(
            rule_id="rule", severity="critical", path="example.py",
            start_line=3, start_column=1, end_line=3, end_column=16,
            message="Avoid exec.", code=None, metadata=metadata,
            raw_reference="/results/0",
        )
        self.assertEqual(metadata, {"cwe": ["CWE-78"]})


class ScanDocumentTests(unittest.TestCase):
    def test_document_has_fixed_schema_and_scan_metadata(self) -> None:
        payload = ScanDocument.create("1.163.0", ".", []).to_dict()
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["scan"]["tool"], "semgrep")
        self.assertEqual(payload["scan"]["ruleset"], "p/security-audit")
        self.assertEqual(payload["scan"]["tool_version"], "1.163.0")


if __name__ == "__main__":
    unittest.main()
