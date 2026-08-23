import hashlib
import json
import unittest

from reporting.manifest import manifest_entry, render_manifest


class ManifestTests(unittest.TestCase):
    def test_entry_records_bytes_and_sha256(self) -> None:
        data = b"hello"
        entry = manifest_entry("security-report.json", data)
        self.assertEqual(entry["path"], "security-report.json")
        self.assertEqual(entry["bytes"], 5)
        self.assertEqual(entry["sha256"], hashlib.sha256(data).hexdigest())

    def test_render_manifest_is_parseable_and_inventories(self) -> None:
        payload = json.loads(
            render_manifest(
                [("security-report.json", b"{}"), ("security-report.md", b"# x")]
            )
        )
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(
            [artifact["path"] for artifact in payload["artifacts"]],
            ["security-report.json", "security-report.md"],
        )
        for artifact in payload["artifacts"]:
            self.assertEqual(len(artifact["sha256"]), 64)
            self.assertIsInstance(artifact["bytes"], int)


if __name__ == "__main__":
    unittest.main()
