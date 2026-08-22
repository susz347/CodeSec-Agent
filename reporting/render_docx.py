from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from reporting.errors import ReportRenderError
from reporting.models import SecurityReport
from reporting.render_json import report_dict


def render_docx(report: SecurityReport) -> bytes:
    node = os.environ.get("CODESEC_NODE") or shutil.which("node")
    if not node:
        raise ReportRenderError(
            "DOCX rendering requires Node.js and npm install --ignore-scripts."
        )
    script = Path(__file__).with_suffix(".js")
    payload = json.dumps(report_dict(report), ensure_ascii=False).encode("utf-8")
    try:
        process = subprocess.run(
            [node, str(script)],
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise ReportRenderError("Cannot start the DOCX renderer.") from error
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise ReportRenderError(f"DOCX rendering failed: {detail or 'unknown error'}")
    if not process.stdout.startswith(b"PK"):
        raise ReportRenderError("DOCX renderer returned an invalid document.")
    return process.stdout
