import unittest

from agent.llm import (
    EvidenceRef,
    LlmFormatError,
    build_llm_request,
    parse_llm_response,
)
from agent.security_reviewer import LlmReviewer


def finding(
    identifier: str = "f1",
    path: str = "app.py",
    start: int = 3,
    end: int = 3,
    severity: str = "error",
) -> dict[str, object]:
    return {
        "id": identifier,
        "tool": "semgrep",
        "rule_id": "python.lang.security.audit.exec-used",
        "severity": severity,
        "path": path,
        "start_line": start,
        "start_column": None,
        "end_line": end,
        "end_column": None,
        "message": "Avoid exec.",
        "code": "exec(user_input)",
        "metadata": {},
        "raw_reference": "/results/0",
    }


def verdict_payload(
    finding_id: str = "f1", label: str = "confirmed", refs: list[dict] | None = None
) -> dict[str, object]:
    item: dict[str, object] = {
        "finding_id": finding_id,
        "label": label,
        "title": "title",
        "cause": "cause",
        "impact": "impact",
        "remediation": "remediation",
        "references": ["CWE-78"],
    }
    if refs is not None:
        item["evidence_refs"] = refs
    return {"schema_version": "1.0", "items": [item]}


class FakeClient:
    def __init__(self, response: dict[str, object]) -> None:
        self._response = response
        self.requests: list[dict] = []

    def complete(self, request: dict) -> dict[str, object]:
        self.requests.append(request)
        return self._response


class BuildLlmRequestTests(unittest.TestCase):
    def test_includes_finding_fields(self) -> None:
        request = build_llm_request([finding()])
        self.assertEqual(request["schema_version"], "1.0")
        item = request["findings"][0]
        self.assertEqual(item["finding_id"], "f1")
        self.assertEqual(item["rule_id"], "python.lang.security.audit.exec-used")
        self.assertIsNone(item["context"])

    def test_includes_context_when_evidence_present(self) -> None:
        request = build_llm_request(
            [finding()], evidence={"f1": {"path": "app.py", "start_line": 1, "end_line": 3}}
        )
        self.assertEqual(request["findings"][0]["context"]["start_line"], 1)


class ParseLlmResponseTests(unittest.TestCase):
    def test_parses_valid_response(self) -> None:
        payload = verdict_payload("f1", "confirmed", [{"path": "app.py", "start_line": 3, "end_line": 3}])
        verdicts = parse_llm_response(payload, [finding()])
        self.assertEqual(len(verdicts), 1)
        self.assertEqual(verdicts[0].label, "confirmed")
        self.assertEqual(verdicts[0].evidence_refs, (EvidenceRef("app.py", 3, 3),))

    def test_rejects_bad_schema(self) -> None:
        with self.assertRaises(LlmFormatError):
            parse_llm_response({"schema_version": "2.0", "items": []}, [finding()])

    def test_rejects_unknown_finding_id(self) -> None:
        with self.assertRaises(LlmFormatError):
            parse_llm_response(verdict_payload("nope"), [finding()])

    def test_rejects_invalid_label(self) -> None:
        with self.assertRaises(LlmFormatError):
            parse_llm_response(verdict_payload("f1", "critical"), [finding()])

    def test_rejects_confirmed_without_evidence_refs(self) -> None:
        with self.assertRaises(LlmFormatError):
            parse_llm_response(verdict_payload("f1", "confirmed", []), [finding()])

    def test_allows_suspicious_without_evidence_refs(self) -> None:
        verdicts = parse_llm_response(verdict_payload("f1", "suspicious", []), [finding()])
        self.assertEqual(verdicts[0].label, "suspicious")

    def test_rejects_ref_out_of_verifiable_range(self) -> None:
        with self.assertRaises(LlmFormatError):
            parse_llm_response(
                verdict_payload("f1", "confirmed", [{"path": "app.py", "start_line": 9, "end_line": 9}]),
                [finding()],
            )

    def test_rejects_ref_path_mismatch(self) -> None:
        with self.assertRaises(LlmFormatError):
            parse_llm_response(
                verdict_payload("f1", "confirmed", [{"path": "other.py", "start_line": 3, "end_line": 3}]),
                [finding()],
            )

    def test_accepts_ref_within_evidence_window(self) -> None:
        evidence = {"f1": {"path": "app.py", "start_line": 1, "end_line": 10}}
        payload = verdict_payload("f1", "confirmed", [{"path": "app.py", "start_line": 1, "end_line": 10}])
        verdicts = parse_llm_response(payload, [finding()], evidence)
        self.assertEqual(verdicts[0].evidence_refs[0].start_line, 1)

    def test_rejects_ref_beyond_evidence_window(self) -> None:
        evidence = {"f1": {"path": "app.py", "start_line": 1, "end_line": 10}}
        payload = verdict_payload("f1", "confirmed", [{"path": "app.py", "start_line": 11, "end_line": 11}])
        with self.assertRaises(LlmFormatError):
            parse_llm_response(payload, [finding()], evidence)


class LlmReviewerTests(unittest.TestCase):
    def test_requires_client(self) -> None:
        with self.assertRaises(NotImplementedError):
            LlmReviewer().analyze([finding()])

    def test_produces_analysis_with_evidence_refs(self) -> None:
        client = FakeClient(
            verdict_payload("f1", "confirmed", [{"path": "app.py", "start_line": 3, "end_line": 3}])
        )
        document = LlmReviewer(client).analyze(
            [finding()], evidence={"f1": {"path": "app.py", "start_line": 1, "end_line": 3}}
        )
        self.assertEqual(document.backend, "deepseek")
        item = document.items[0]
        self.assertEqual(item.label, "confirmed")
        self.assertEqual(item.evidence_refs, ({"path": "app.py", "start_line": 3, "end_line": 3},))

    def test_falls_back_for_uncovered_finding(self) -> None:
        client = FakeClient(verdict_payload("f1", "suspicious", []))
        document = LlmReviewer(client).analyze([finding("f1"), finding("f2")])
        by_id = {item.finding_id: item for item in document.items}
        self.assertEqual(by_id["f1"].label, "suspicious")
        self.assertEqual(by_id["f2"].label, "confirmed")  # deterministic fallback

    def test_no_network_or_api_key_needed(self) -> None:
        # A fake in-process client satisfies the full contract without I/O.
        client = FakeClient(verdict_payload("f1", "suspicious", []))
        document = LlmReviewer(client).analyze([finding()])
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(len(document.items), 1)


if __name__ == "__main__":
    unittest.main()
