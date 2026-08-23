import unittest

from agent.models import AnalysisDocument, AnalysisFormatError, AnalysisItem


def item(finding_id: str = "f1", label: str = "confirmed") -> AnalysisItem:
    return AnalysisItem(
        finding_id=finding_id,
        label=label,
        title="title",
        cause="cause",
        impact="impact",
        remediation="remediation",
        references=("CWE-78",),
    )


class AnalysisItemTests(unittest.TestCase):
    def test_rejects_unknown_label(self) -> None:
        with self.assertRaises(AnalysisFormatError):
            AnalysisItem(
                finding_id="f", label="nope", title="", cause="",
                impact="", remediation="", references=(),
            )

    def test_to_dict_serializes_references_as_list(self) -> None:
        value = item().to_dict()
        self.assertEqual(value["finding_id"], "f1")
        self.assertEqual(value["label"], "confirmed")
        self.assertEqual(value["references"], ["CWE-78"])

    def test_diff_status_defaults_to_unknown(self) -> None:
        self.assertEqual(item().diff_status, "unknown")
        self.assertEqual(item().to_dict()["diff_status"], "unknown")

    def test_baseline_status_defaults_to_unknown(self) -> None:
        self.assertEqual(item().baseline_status, "unknown")
        self.assertEqual(item().to_dict()["baseline_status"], "unknown")

    def test_rejects_unknown_diff_status(self) -> None:
        with self.assertRaises(AnalysisFormatError):
            AnalysisItem(
                finding_id="f", label="confirmed", title="", cause="",
                impact="", remediation="", references=(), diff_status="new",
            )

    def test_rejects_unknown_baseline_status(self) -> None:
        with self.assertRaises(AnalysisFormatError):
            AnalysisItem(
                finding_id="f", label="confirmed", title="", cause="",
                impact="", remediation="", references=(), baseline_status="old",
            )

    def test_to_dict_includes_evidence_when_present(self) -> None:
        evidence = {"path": "app.py", "start_line": 1, "end_line": 3}
        value = AnalysisItem(
            finding_id="f", label="confirmed", title="", cause="",
            impact="", remediation="", references=(),
            diff_status="changed", evidence=evidence,
        ).to_dict()
        self.assertEqual(value["diff_status"], "changed")
        self.assertEqual(value["evidence"], evidence)

    def test_to_dict_omits_evidence_when_none(self) -> None:
        self.assertNotIn("evidence", item().to_dict())


class AnalysisDocumentTests(unittest.TestCase):
    def test_create_and_to_dict(self) -> None:
        document = AnalysisDocument.create("deterministic", [item()])
        self.assertEqual(document.schema_version, "1.0")
        self.assertEqual(document.backend, "deterministic")
        self.assertEqual(len(document.items), 1)

    def test_from_dict_roundtrip(self) -> None:
        original = AnalysisDocument.create("deterministic", [item()])
        restored = AnalysisDocument.from_dict(original.to_dict())
        self.assertEqual(restored.to_dict(), original.to_dict())

    def test_from_dict_rejects_bad_schema(self) -> None:
        with self.assertRaises(AnalysisFormatError):
            AnalysisDocument.from_dict({"schema_version": "2.0", "items": []})

    def test_from_dict_rejects_invalid_label(self) -> None:
        payload = {
            "schema_version": "1.0",
            "items": [{"finding_id": "f", "label": "bad"}],
        }
        with self.assertRaises(AnalysisFormatError):
            AnalysisDocument.from_dict(payload)

    def test_from_dict_rejects_missing_finding_id(self) -> None:
        payload = {"schema_version": "1.0", "items": [{"label": "confirmed"}]}
        with self.assertRaises(AnalysisFormatError):
            AnalysisDocument.from_dict(payload)

    def test_from_dict_accepts_legacy_item_without_new_fields(self) -> None:
        payload = {
            "schema_version": "1.0",
            "items": [{"finding_id": "f", "label": "confirmed"}],
        }
        document = AnalysisDocument.from_dict(payload)
        self.assertEqual(document.items[0].diff_status, "unknown")
        self.assertEqual(document.items[0].baseline_status, "unknown")
        self.assertIsNone(document.items[0].evidence)

    def test_from_dict_roundtrip_with_evidence(self) -> None:
        original = AnalysisDocument.create(
            "deterministic",
            [
                AnalysisItem(
                    finding_id="f", label="confirmed", title="", cause="",
                    impact="", remediation="", references=(),
                    diff_status="changed", evidence={"path": "app.py"},
                )
            ],
        )
        restored = AnalysisDocument.from_dict(original.to_dict())
        self.assertEqual(restored.items[0].diff_status, "changed")
        self.assertEqual(restored.items[0].evidence, {"path": "app.py"})


if __name__ == "__main__":
    unittest.main()
