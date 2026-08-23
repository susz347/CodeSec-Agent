import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]


def _workflow(name: str) -> str:
    return (_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


class WorkflowTests(unittest.TestCase):
    def test_security_scan_builds_and_passes_pr_diff(self) -> None:
        workflow = _workflow("security-scan.yml")
        self.assertIn("github.event.pull_request.base.sha", workflow)
        self.assertIn("github.event.pull_request.head.sha", workflow)
        self.assertIn("artifacts/pr.diff", workflow)
        self.assertIn("--repo-root .", workflow)
        self.assertIn("--diff artifacts/pr.diff", workflow)

    def test_security_scan_limits_diff_to_pull_requests(self) -> None:
        workflow = _workflow("security-scan.yml")
        self.assertIn("if: github.event_name == 'pull_request'", workflow)

    def test_security_scan_uses_versioned_triage_store_when_present(self) -> None:
        workflow = _workflow("security-scan.yml")
        self.assertIn(".codesec/triage.json", workflow)
        self.assertIn("--triage-store .codesec/triage.json", workflow)

    def test_test_workflow_runs_complete_unittest_suite(self) -> None:
        workflow = _workflow("test.yml")
        self.assertIn("python-version: \"3.12\"", workflow)
        self.assertIn("node-version: \"20\"", workflow)
        self.assertIn("npm install --ignore-scripts", workflow)
        self.assertIn("python -m unittest discover -v", workflow)


if __name__ == "__main__":
    unittest.main()
