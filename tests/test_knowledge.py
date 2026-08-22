import unittest

from agent.knowledge import HIGH_CONFIDENCE, lookup, signature


class SignatureTests(unittest.TestCase):
    def test_semgrep_freeform_rule_maps_to_concept(self) -> None:
        self.assertEqual(
            signature({"tool": "semgrep", "rule_id": "python.lang.security.audit.exec-used"}),
            "exec-used",
        )

    def test_bandit_opaque_id_maps_to_concept(self) -> None:
        self.assertEqual(signature({"tool": "bandit", "rule_id": "B608"}), "sql-injection")

    def test_npm_audit_maps_to_dependency(self) -> None:
        self.assertEqual(signature({"tool": "npm-audit", "rule_id": "npm-audit/lodash"}), "dependency")


class LookupTests(unittest.TestCase):
    def test_semgrep_exec_maps_to_cwe78(self) -> None:
        knowledge = lookup(
            {"tool": "semgrep", "rule_id": "python.lang.security.audit.exec-used", "metadata": {}}
        )
        self.assertEqual(knowledge.cwe, "CWE-78")
        self.assertEqual(knowledge.owasp, "A03:2021 Injection")

    def test_bandit_subprocess_maps_to_cwe78(self) -> None:
        self.assertEqual(lookup({"tool": "bandit", "rule_id": "B602", "metadata": {}}).cwe, "CWE-78")

    def test_bandit_hardcoded_secret_maps_to_cwe798(self) -> None:
        self.assertEqual(lookup({"tool": "bandit", "rule_id": "B105", "metadata": {}}).cwe, "CWE-798")

    def test_npm_audit_uses_metadata_cwe(self) -> None:
        knowledge = lookup(
            {"tool": "npm-audit", "rule_id": "npm-audit/lodash", "metadata": {"cwe": ["CWE-1321"]}}
        )
        self.assertEqual(knowledge.cwe, "CWE-1321")

    def test_npm_audit_falls_back_to_cwe937(self) -> None:
        knowledge = lookup({"tool": "npm-audit", "rule_id": "npm-audit/lodash", "metadata": {}})
        self.assertEqual(knowledge.cwe, "CWE-937")

    def test_unknown_rule_falls_back(self) -> None:
        knowledge = lookup({"tool": "semgrep", "rule_id": "some.unknown.rule", "metadata": {}})
        self.assertEqual(knowledge.cwe, "CWE-unknown")

    def test_high_confidence_includes_exec(self) -> None:
        self.assertIn("exec-used", HIGH_CONFIDENCE)


if __name__ == "__main__":
    unittest.main()
