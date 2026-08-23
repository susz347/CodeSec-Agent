import unittest
from unittest.mock import patch

from agent.llm import (
    DeepSeekClient,
    EvidenceRef,
    LlmFormatError,
    LlmTransportError,
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


class _HttpResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "_HttpResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


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


class DeepSeekClientTests(unittest.TestCase):
    def test_posts_json_mode_and_extracts_completion_content(self) -> None:
        response = _HttpResponse(
            b'{"choices":[{"message":{"content":"{\\"schema_version\\":\\"1.0\\",\\"items\\":[]}"}}]}'
        )
        with patch("agent.llm.urlopen", return_value=response) as urlopen:
            payload = DeepSeekClient("test-key", timeout_seconds=7).complete(
                {"schema_version": "1.0", "findings": []}
            )

        request = urlopen.call_args.args[0]
        body = request.data.decode("utf-8")
        self.assertEqual(request.full_url, "https://api.deepseek.com/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertIn('"response_format": {"type": "json_object"}', body)
        self.assertIn('"max_tokens": 1200', body)
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 7)
        self.assertEqual(payload, {"schema_version": "1.0", "items": []})


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
    @staticmethod
    def _complete_evidence(identifier: str = "f1") -> dict[str, dict[str, object]]:
        return {
            identifier: {
                "path": "app.py", "start_line": 1, "end_line": 3,
                "snippet": "one\ntwo\nexec(user_input)\n", "sha256": "a" * 64,
                "truncated": False,
            }
        }

    def test_requires_client(self) -> None:
        with self.assertRaises(NotImplementedError):
            LlmReviewer().analyze([finding()])

    def test_produces_analysis_with_evidence_refs(self) -> None:
        client = FakeClient(
            verdict_payload("f1", "confirmed", [{"path": "app.py", "start_line": 3, "end_line": 3}])
        )
        document = LlmReviewer(client).analyze(
            [finding()], diff_statuses={"f1": "changed"}, baseline_statuses={"f1": "new"},
            evidence=self._complete_evidence(),
        )
        self.assertEqual(document.backend, "deepseek-gated")
        item = document.items[0]
        self.assertEqual(item.label, "confirmed")
        self.assertEqual(item.evidence_refs, ({"path": "app.py", "start_line": 3, "end_line": 3},))

    def test_falls_back_for_uncovered_finding(self) -> None:
        client = FakeClient(verdict_payload("f1", "suspicious", []))
        document = LlmReviewer(client).analyze(
            [finding("f1"), finding("f2")],
            diff_statuses={"f1": "changed", "f2": "changed"},
            baseline_statuses={"f1": "new", "f2": "existing"},
            evidence=self._complete_evidence(),
        )
        by_id = {item.finding_id: item for item in document.items}
        self.assertEqual(by_id["f1"].label, "suspicious")
        self.assertEqual(by_id["f2"].label, "confirmed")  # deterministic fallback

    def test_no_network_or_api_key_needed(self) -> None:
        # A fake in-process client satisfies the full contract without I/O.
        client = FakeClient(verdict_payload("f1", "suspicious", []))
        document = LlmReviewer(client).analyze(
            [finding()], diff_statuses={"f1": "changed"}, baseline_statuses={"f1": "new"},
            evidence=self._complete_evidence(),
        )
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(len(document.items), 1)

    def test_gates_requests_and_falls_back_per_finding(self) -> None:
        client = FakeClient(
            verdict_payload(
                "candidate", "confirmed",
                [{"path": "app.py", "start_line": 3, "end_line": 3}],
            )
        )
        document = LlmReviewer(client).analyze(
            [finding("candidate"), finding("existing")],
            diff_statuses={"candidate": "changed", "existing": "changed"},
            baseline_statuses={"candidate": "new", "existing": "existing"},
            evidence={
                "candidate": {
                    "path": "app.py", "start_line": 1, "end_line": 3,
                    "snippet": "one\ntwo\nexec(user_input)\n", "sha256": "a" * 64,
                    "truncated": False,
                },
                "existing": {
                    "path": "app.py", "start_line": 1, "end_line": 3,
                    "snippet": "one\ntwo\nexec(user_input)\n", "sha256": "b" * 64,
                    "truncated": False,
                },
            },
        )

        self.assertEqual(
            [item["finding_id"] for item in client.requests[0]["findings"]], ["candidate"]
        )
        by_id = {item.finding_id: item for item in document.items}
        self.assertEqual(by_id["candidate"].label, "confirmed")
        self.assertEqual(by_id["existing"].label, "confirmed")

    def test_transport_failure_keeps_deterministic_result(self) -> None:
        class FailingClient:
            def complete(self, request: dict) -> dict:
                raise LlmTransportError("unavailable")

        document = LlmReviewer(FailingClient()).analyze(
            [finding()], diff_statuses={"f1": "changed"}, baseline_statuses={"f1": "new"},
            evidence=self._complete_evidence(),
        )
        self.assertEqual(document.backend, "deterministic")
        self.assertEqual(document.items[0].label, "confirmed")

    def test_invalid_model_item_falls_back_without_discarding_valid_item(self) -> None:
        client = FakeClient(
            {
                "schema_version": "1.0",
                "items": [
                    verdict_payload("f1", "suspicious", [])["items"][0],
                    verdict_payload(
                        "f2", "confirmed",
                        [{"path": "other.py", "start_line": 3, "end_line": 3}],
                    )["items"][0],
                ],
            }
        )
        evidence = self._complete_evidence("f1")
        evidence.update(self._complete_evidence("f2"))
        document = LlmReviewer(client).analyze(
            [finding("f1"), finding("f2")],
            diff_statuses={"f1": "changed", "f2": "changed"},
            baseline_statuses={"f1": "new", "f2": "new"},
            evidence=evidence,
        )
        by_id = {item.finding_id: item for item in document.items}
        self.assertEqual(by_id["f1"].label, "suspicious")
        self.assertEqual(by_id["f2"].label, "confirmed")

    def test_caps_gated_batch_to_ten_findings(self) -> None:
        client = FakeClient({"schema_version": "1.0", "items": []})
        findings = [finding(f"f{index}") for index in range(11)]
        evidence = {
            f"f{index}": {
                "path": "app.py", "start_line": 1, "end_line": 3,
                "snippet": "one\ntwo\nexec(user_input)\n", "sha256": "a" * 64,
                "truncated": False,
            }
            for index in range(11)
        }
        LlmReviewer(client).analyze(
            findings,
            diff_statuses={f"f{index}": "changed" for index in range(11)},
            baseline_statuses={f"f{index}": "new" for index in range(11)},
            evidence=evidence,
        )
        self.assertEqual(len(client.requests[0]["findings"]), 10)


if __name__ == "__main__":
    unittest.main()
