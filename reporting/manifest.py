"""Artifact governance: a verifiable inventory of generated report files.

The manifest lists every file the reporting CLI writes, with byte size and
SHA-256, so a consumer (human or CI) can verify that the set and content of
artifacts match what was produced. It is written atomically alongside the
reports it inventories.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Sequence


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_entry(name: str, data: bytes) -> dict[str, object]:
    return {"path": name, "bytes": len(data), "sha256": _sha256(data)}


def render_manifest(entries: Sequence[tuple[str, bytes]]) -> str:
    """Serialize an inventory of (name, bytes) artifacts as schema 1.0 JSON."""
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "schema_version": "1.0",
        "generated_at": timestamp,
        "artifacts": [manifest_entry(name, data) for name, data in entries],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
