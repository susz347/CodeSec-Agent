import json
import tempfile
import unittest
from pathlib import Path

from agent.cli import main
from agent.triage import build_baseline, save


def _finding() -> dict[str, object]:
    return {
        "id": "f1",
        "tool": "semgrep",
        "rule_id": "python.lang.security.audit.exec-used",
        "severity": "error",
        "path": "app.py",
        "start_line": 3,
        "end_line": 3,
        "message": "Avoid exec.",
        "code": "exec(user_input)",
        "metadata": {},
        "raw_reference": "/results/0",
    }


class AgentCliTests(unittest.TestCase):
    def test_triage_store_marks_existing_finding_in_analysis_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            finding = _finding()
            input_path = root / "findings.json"
            input_path.write_text(
                json.dumps({"schema_version": "1.0", "findings": [finding]}),
                encoding="utf-8",
            )
            store = root / ".codesec" / "triage.json"
            save(store, build_baseline([finding]))
            output_dir = root / "artifacts"

            self.assertEqual(
                main([
                    "--input", str(input_path), "--output-dir", str(output_dir),
                    "--triage-store", str(store),
                ]),
                0,
            )
            output = json.loads((output_dir / "analysis.json").read_text(encoding="utf-8"))
            self.assertEqual(output["items"][0]["baseline_status"], "existing")


if __name__ == "__main__":
    unittest.main()
