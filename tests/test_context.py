import os
import tempfile
import unittest
from pathlib import Path
from typing import Iterable

from agent.context import ContextError, PathEscapeError, _collect_window, read_context


def _finding(path: str = "app.py", start: int = 15, end: int = 16) -> dict[str, object]:
    return {
        "id": "f1",
        "path": path,
        "start_line": start,
        "end_line": end,
    }


def _supports_symlinks() -> bool:
    with tempfile.TemporaryDirectory() as directory:
        try:
            os.symlink("target", os.path.join(directory, "link"))
            return True
        except (OSError, NotImplementedError):
            return False


class ReadContextTests(unittest.TestCase):
    def test_reads_window_within_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text(
                "".join(f"line {index}\n" for index in range(1, 31)), encoding="utf-8"
            )
            evidence = read_context(
                _finding(start=15, end=16), root, lines_before=2, lines_after=2
            )
            self.assertEqual(evidence.start_line, 13)
            self.assertEqual(evidence.end_line, 18)
            self.assertIn("line 15", evidence.snippet)
            self.assertFalse(evidence.truncated)

    def test_sha256_matches_snippet(self) -> None:
        import hashlib

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("a\nb\nc\n", encoding="utf-8")
            evidence = read_context(_finding(start=2, end=2), root, lines_before=0, lines_after=0)
            self.assertEqual(
                evidence.sha256, hashlib.sha256(evidence.snippet.encode("utf-8")).hexdigest()
            )

    def test_rejects_parent_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(PathEscapeError):
                read_context(_finding(path="../secret.txt"), root)

    def test_rejects_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            absolute = str((root / "app.py").resolve())
            with self.assertRaises(PathEscapeError):
                read_context(_finding(path=absolute), root)

    def test_rejects_windows_drive_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(PathEscapeError):
                read_context(_finding(path="C:\\Windows\\win.ini"), root)

    @unittest.skipUnless(_supports_symlinks(), "symlinks not supported")
    def test_rejects_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            root.mkdir()
            (base / "secret.txt").write_text("secret", encoding="utf-8")
            (root / "link.txt").symlink_to(base / "secret.txt")
            with self.assertRaises(PathEscapeError):
                read_context(_finding(path="link.txt"), root)

    def test_missing_file_raises_context_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ContextError):
                read_context(_finding(path="nope.py"), Path(directory))

    def test_repo_root_must_be_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "not_a_dir"
            file.write_text("x", encoding="utf-8")
            with self.assertRaises(ContextError):
                read_context(_finding(), file)

    def test_truncates_large_snippet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("x" * 10000 + "\n", encoding="utf-8")
            evidence = read_context(_finding(start=1, end=1), root, lines_before=0, lines_after=0, max_bytes=100)
            self.assertTrue(evidence.truncated)
            self.assertLessEqual(len(evidence.snippet.encode("utf-8")), 100)

    def test_clamps_at_file_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("a\nb\nc\n", encoding="utf-8")
            evidence = read_context(_finding(start=2, end=3), root, lines_before=5, lines_after=5)
            self.assertEqual(evidence.start_line, 1)
            self.assertEqual(evidence.end_line, 3)

    def test_out_of_range_raises_context_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("a\n", encoding="utf-8")
            with self.assertRaises(ContextError):
                read_context(_finding(start=10, end=10), root)


class CollectWindowTests(unittest.TestCase):
    def test_stops_reading_at_line_window(self) -> None:
        consumed: list[int] = []

        def source() -> Iterable[str]:
            for index in range(1, 1001):
                consumed.append(index)
                yield f"line {index}\n"

        selected, truncated, last = _collect_window(
            source(), path="app.py", window_start=3, window_end=7, start_line=5, max_bytes=8192
        )
        self.assertEqual(consumed[-1], 8)
        self.assertEqual(last, 7)
        self.assertEqual(len(selected), 5)
        self.assertFalse(truncated)

    def test_stops_reading_at_byte_limit(self) -> None:
        consumed: list[int] = []

        def source() -> Iterable[str]:
            for index in range(1, 1001):
                consumed.append(index)
                yield ("x" * 500) + "\n"

        selected, truncated, last = _collect_window(
            source(), path="app.py", window_start=1, window_end=1000, start_line=1, max_bytes=100
        )
        self.assertTrue(truncated)
        self.assertEqual(consumed, [1])
        self.assertEqual(selected, [])


if __name__ == "__main__":
    unittest.main()
