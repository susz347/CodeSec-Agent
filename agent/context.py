"""Safely read bounded local code context around a finding.

This is the only analysis module that reads source files. It enforces a strict
path-safety boundary: no read may escape the repository root, whether via
relative traversal (``..``), absolute paths, or symlinks. Callers catch
``ContextError`` and skip a finding's evidence; they must never read outside
``repo_root``.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

DEFAULT_LINES_BEFORE = 10
DEFAULT_LINES_AFTER = 10
DEFAULT_MAX_BYTES = 8192


class ContextError(Exception):
    """Base error for context reading failures."""


class PathEscapeError(ContextError):
    """Raised when a finding path resolves outside the repository root."""


@dataclass(frozen=True)
class ContextEvidence:
    """Structured, machine-verifiable local code context for one finding."""

    finding_id: str
    path: str
    start_line: int
    end_line: int
    lines_before: int
    lines_after: int
    truncated: bool
    snippet: str
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "lines_before": self.lines_before,
            "lines_after": self.lines_after,
            "truncated": self.truncated,
            "snippet": self.snippet,
            "sha256": self.sha256,
        }


def _resolve_repo_root(repo_root: Path) -> Path:
    root = Path(repo_root).resolve()
    if not root.is_dir():
        raise ContextError(f"Repository root is not a directory: {repo_root}")
    return root


def _validate_relative_path(path: str) -> None:
    raw = Path(path)
    if raw.is_absolute():
        raise PathEscapeError(f"Absolute finding path is not allowed: {path}")
    # Reject Windows drive letters and UNC paths even on POSIX, where Path does
    # not consider "C:\\x" or "//server/share" absolute.
    if ":" in raw.parts[0] or path.startswith(("//", "\\\\")):
        raise PathEscapeError(f"Absolute finding path is not allowed: {path}")
    if ".." in raw.parts:
        raise PathEscapeError(f"Finding path escapes repository root: {path}")


def read_context(
    finding: dict[str, Any],
    repo_root: str | Path,
    *,
    lines_before: int = DEFAULT_LINES_BEFORE,
    lines_after: int = DEFAULT_LINES_AFTER,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> ContextEvidence:
    """Read a bounded window of source lines around a finding.

    Raises ``PathEscapeError`` when the finding path escapes ``repo_root`` and
    ``ContextError`` for other read failures. Never reads outside ``repo_root``.
    """
    root = _resolve_repo_root(Path(repo_root))
    path = str(finding.get("path", ""))
    _validate_relative_path(path)

    candidate = (root / path).resolve()
    if not candidate.is_relative_to(root):
        raise PathEscapeError(f"Finding path escapes repository root: {path}")
    if not candidate.is_file():
        raise ContextError(f"Finding path is not a file: {path}")

    start_line = int(finding.get("start_line", 1))
    end_line = int(finding.get("end_line", start_line))
    window_start = max(1, start_line - lines_before)
    window_end = end_line + lines_after

    try:
        with candidate.open("r", encoding="utf-8", errors="replace") as handle:
            all_lines = handle.readlines()
    except OSError as error:
        raise ContextError(f"Cannot read finding source: {path}") from error

    if start_line > len(all_lines):
        raise ContextError(f"Finding lines out of range: {path}")

    snippet = "".join(all_lines[window_start - 1 : window_end])
    truncated = False
    if len(snippet.encode("utf-8")) > max_bytes:
        snippet = snippet.encode("utf-8")[:max_bytes].decode("utf-8", errors="replace")
        truncated = True

    return ContextEvidence(
        finding_id=str(finding["id"]),
        path=path,
        start_line=window_start,
        end_line=min(window_end, len(all_lines)),
        lines_before=lines_before,
        lines_after=lines_after,
        truncated=truncated,
        snippet=snippet,
        sha256=sha256(snippet.encode("utf-8")).hexdigest(),
    )
