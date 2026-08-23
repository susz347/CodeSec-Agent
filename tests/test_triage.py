import unittest
import tempfile
from pathlib import Path

from agent.triage import (
    add_disposition,
    build_baseline,
    compare_findings,
    fingerprint,
    statistics,
)


def finding(identifier: str = "f1", line: int = 10, code: str = "exec(value)") -> dict[str, object]:
    return {
        "id": identifier,
        "tool": "semgrep",
        "rule_id": "python.lang.security.audit.exec-used",
        "path": "src/app.py",
        "start_line": line,
        "end_line": line,
        "code": code,
        "message": "Avoid exec.",
    }


class TriageTests(unittest.TestCase):
    def test_fingerprint_ignores_line_number(self) -> None:
        self.assertEqual(fingerprint(finding(line=10)), fingerprint(finding(line=100)))

    def test_compare_marks_new_existing_and_resolved(self) -> None:
        old = finding("old")
        removed = finding("removed", code="eval(value)")
        baseline = build_baseline([old, removed])
        result = compare_findings([finding("current"), finding("new", code="subprocess.run(x)")], baseline)
        self.assertEqual(result.status_by_id["current"], "existing")
        self.assertEqual(result.status_by_id["new"], "new")
        self.assertEqual(result.resolved, (fingerprint(removed),))

    def test_dispositions_and_statistics_are_grouped(self) -> None:
        document = build_baseline([finding()])
        updated = add_disposition(
            document,
            fingerprint=fingerprint(finding()),
            resolution="false_positive",
            reviewer="alice",
            machine_label="confirmed",
        )
        values = statistics(updated)
        self.assertEqual(values["total"], 1)
        self.assertEqual(values["by_rule"]["semgrep:python.lang.security.audit.exec-used"]["false_positive"], 1)


class TriageCliTests(unittest.TestCase):
    def test_baseline_disposition_and_stats_commands(self) -> None:
        from agent.triage_cli import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            findings = root / "findings.json"
            store = root / ".codesec" / "triage.json"
            findings.write_text(
                '{"schema_version":"1.0","findings":['
                '{"id":"f1","tool":"semgrep","rule_id":"rule","path":"a.py",'
                '"start_line":1,"end_line":1,"code":"exec(x)","message":"Avoid exec."}]}',
                encoding="utf-8",
            )
            self.assertEqual(main(["baseline", "--input", str(findings), "--store", str(store)]), 0)
            document = __import__("agent.triage", fromlist=["load"]).load(store)
            value = document["baseline"]["findings"][0]["fingerprint"]
            self.assertEqual(main(["disposition", "--store", str(store), "--fingerprint", value, "--resolution", "false_positive", "--reviewer", "alice", "--machine-label", "confirmed"]), 0)
            self.assertEqual(main(["stats", "--store", str(store)]), 0)


if __name__ == "__main__":
    unittest.main()
