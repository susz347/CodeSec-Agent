import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from agent.triage import (
    add_disposition,
    build_baseline,
    compare_findings,
    fingerprint,
    load,
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

    def test_new_finding_disposition_stores_only_safe_identity(self) -> None:
        baseline_finding = finding("baseline")
        new_finding = finding("new", code="eval(value)")
        updated = add_disposition(
            build_baseline([baseline_finding]),
            fingerprint=fingerprint(new_finding),
            finding=new_finding,
            resolution="true_positive",
            reviewer="alice",
            machine_label="confirmed",
            note="Validated without storing source evidence.",
        )
        disposition = updated["dispositions"][0]
        self.assertEqual(disposition["fingerprint"], fingerprint(new_finding))
        self.assertEqual(disposition["tool"], "semgrep")
        self.assertEqual(disposition["rule_id"], "python.lang.security.audit.exec-used")
        self.assertNotIn("path", disposition)
        self.assertNotIn("code", disposition)
        self.assertEqual(
            statistics(updated)["by_rule"]["semgrep:python.lang.security.audit.exec-used"],
            {"true_positive": 1},
        )


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

    def test_new_finding_disposition_command_uses_normalized_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline_input = root / "baseline.json"
            current_input = root / "current.json"
            store = root / ".codesec" / "triage.json"
            baseline_input.write_text(
                '{"schema_version":"1.0","findings":['
                '{"id":"f-baseline","tool":"semgrep","rule_id":"rule","path":"a.py",'
                '"start_line":1,"end_line":1,"code":"exec(x)","message":"Avoid exec."}]}',
                encoding="utf-8",
            )
            current_input.write_text(
                '{"schema_version":"1.0","findings":['
                '{"id":"f-new","tool":"semgrep","rule_id":"new-rule","path":"b.py",'
                '"start_line":1,"end_line":1,"code":"eval(x)","message":"Avoid eval."}]}',
                encoding="utf-8",
            )
            command = [sys.executable, "-m", "agent.triage_cli"]
            project_root = Path(__file__).resolve().parents[1]
            baseline = subprocess.run(
                command + ["baseline", "--input", str(baseline_input), "--store", str(store)],
                capture_output=True,
                text=True,
                cwd=project_root,
                check=False,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr)
            disposition = subprocess.run(
                command + [
                    "disposition", "--store", str(store), "--input", str(current_input),
                    "--finding-id", "f-new", "--resolution", "true_positive",
                    "--reviewer", "alice", "--machine-label", "confirmed",
                    "--note", "Validated without storing source evidence.",
                ],
                capture_output=True,
                text=True,
                cwd=project_root,
                check=False,
            )
            self.assertEqual(disposition.returncode, 0, disposition.stderr)
            missing = subprocess.run(
                command + [
                    "disposition", "--store", str(store), "--input", str(current_input),
                    "--finding-id", "missing", "--resolution", "true_positive",
                    "--reviewer", "alice", "--machine-label", "confirmed",
                ],
                capture_output=True,
                text=True,
                cwd=project_root,
                check=False,
            )
            self.assertEqual(missing.returncode, 1)
            self.assertIn("Expected exactly one finding with id: missing", missing.stderr)
            values = statistics(load(store))
            self.assertEqual(values["total"], 1)
            self.assertEqual(values["by_rule"]["semgrep:new-rule"], {"true_positive": 1})

    def test_new_finding_disposition_command_rejects_duplicate_ids(self) -> None:
        from agent.triage_cli import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "findings.json"
            store = root / ".codesec" / "triage.json"
            input_path.write_text(
                '{"schema_version":"1.0","findings":['
                '{"id":"duplicate","tool":"semgrep","rule_id":"rule-a","path":"a.py",'
                '"start_line":1,"end_line":1,"code":"exec(x)","message":"Avoid exec."},'
                '{"id":"duplicate","tool":"semgrep","rule_id":"rule-b","path":"b.py",'
                '"start_line":1,"end_line":1,"code":"eval(x)","message":"Avoid eval."}]}',
                encoding="utf-8",
            )
            self.assertEqual(
                main(["baseline", "--input", str(input_path), "--store", str(store)]),
                0,
            )
            error = StringIO()
            with redirect_stderr(error):
                self.assertEqual(
                    main([
                        "disposition", "--store", str(store), "--input", str(input_path),
                        "--finding-id", "duplicate", "--resolution", "true_positive",
                        "--reviewer", "alice", "--machine-label", "confirmed",
                    ]),
                    1,
                )
            self.assertIn("Expected exactly one finding with id: duplicate", error.getvalue())
            self.assertEqual(statistics(load(store))["total"], 0)


if __name__ == "__main__":
    unittest.main()
