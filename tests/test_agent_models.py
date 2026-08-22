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


if __name__ == "__main__":
    unittest.main()
