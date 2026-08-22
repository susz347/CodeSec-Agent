import json
import tempfile
import unittest
from pathlib import Path

from reporting.load_findings import ReportInputError, load_documents


def document(tool: str, findings: list[dict[str, object]]) -> dict[str, object]:
    return {"schema_version": "1.0", "scan": {"tool": tool, "tool_version": "1", "ruleset": "rules", "target": ".", "started_at": "2026-08-22T00:00:00Z"}, "findings": findings}


def finding(identifier: str, severity: str, tool: str) -> dict[str, object]:
    return {"id": identifier, "tool": tool, "rule_id": "rule", "severity": severity, "path": "a.py", "start_line": 1, "start_column": None, "end_line": 1, "end_column": None, "message": "message", "code": None, "metadata": {}, "raw_reference": "/results/0"}


class ReportingModelsTests(unittest.TestCase):
    def test_merges_counts_and_sorts_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "a.json", Path(directory) / "b.json"
            first.write_text(json.dumps(document("bandit", [finding("i", "info", "bandit")])), encoding="utf-8")
            second.write_text(json.dumps(document("semgrep", [finding("e", "error", "semgrep")])), encoding="utf-8")
            report = load_documents([first, second])
        self.assertEqual(report.counts, {"error": 1, "warning": 0, "info": 1, "unknown": 0})
        self.assertEqual([item["id"] for item in report.findings], ["e", "i"])
        self.assertEqual(len(report.sources), 2)

    def test_rejects_incompatible_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"schema_version":"2.0","scan":{},"findings":[]}', encoding="utf-8")
            with self.assertRaises(ReportInputError):
                load_documents([path])


if __name__ == "__main__":
    unittest.main()
