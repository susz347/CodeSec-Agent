from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from agent.models import AnalysisDocument
from reporting.errors import ReportRenderError
from reporting.models import SecurityReport
from reporting.render_analysis import analysis_items, evidence_summary
from reporting.risk import order_findings

_FONT_NAME = "CodeSecReport"
_FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)


def _register_font() -> str:
    override = os.environ.get("CODESEC_REPORT_FONT")
    candidates = (Path(override),) if override else _FONT_CANDIDATES
    failures: list[str] = []
    for candidate in candidates:
        if not candidate.is_file():
            failures.append(str(candidate))
            continue
        try:
            pdfmetrics.registerFont(TTFont(_FONT_NAME, str(candidate), subfontIndex=0))
            return _FONT_NAME
        except Exception:
            failures.append(str(candidate))
    checked = ", ".join(failures)
    raise ReportRenderError(f"No usable PDF font found. Checked: {checked}")


def _paragraph(value: object, style: ParagraphStyle) -> Paragraph:
    content = escape("" if value is None else str(value)).replace("\n", "<br/>")
    return Paragraph(content, style)


def render_pdf(report: SecurityReport, analysis: AnalysisDocument | None = None) -> bytes:
    by_id = analysis_items(analysis)
    findings = (
        order_findings(report.findings, by_id) if analysis is not None else report.findings
    )
    font = _register_font()
    title = ParagraphStyle(
        "ReportTitle",
        fontName=font,
        fontSize=20,
        leading=24,
        alignment=1,
        spaceAfter=8 * mm,
    )
    heading = ParagraphStyle(
        "ReportHeading",
        fontName=font,
        fontSize=14,
        leading=18,
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
    )
    finding_heading = ParagraphStyle(
        "FindingHeading",
        fontName=font,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1F4E78"),
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
    body = ParagraphStyle("ReportBody", fontName=font, fontSize=9, leading=12)
    code = ParagraphStyle(
        "ReportCode",
        fontName=font,
        fontSize=8,
        leading=10,
        leftIndent=4 * mm,
        rightIndent=4 * mm,
        borderColor=colors.HexColor("#D9E2F3"),
        borderWidth=0.5,
        borderPadding=4,
        backColor=colors.HexColor("#F5F7FA"),
        spaceBefore=2 * mm,
        spaceAfter=2 * mm,
    )
    table_style = TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), font),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B7C9D6")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )
    story = [
        _paragraph("Security Report", title),
        _paragraph(f"Generated: {report.generated_at}", body),
        _paragraph("Scan Sources", heading),
    ]
    source_rows = [[_paragraph(value, body) for value in ("Tool", "Version", "Ruleset", "Target", "Started At")]]
    source_rows.extend(
        [_paragraph(value, body) for value in (source.tool, source.tool_version, source.ruleset, source.target, source.started_at)]
        for source in report.sources
    )
    source_table = Table(source_rows, colWidths=[23 * mm, 22 * mm, 38 * mm, 45 * mm, 46 * mm], repeatRows=1)
    source_table.setStyle(table_style)
    story.extend([source_table, _paragraph("Summary", heading)])
    summary_rows = [[_paragraph("Severity", body), _paragraph("Count", body)]]
    summary_rows.extend(
        [_paragraph(label, body), _paragraph(value, body)]
        for label, value in (
            ("Total", len(report.findings)),
            ("Error", report.counts["error"]),
            ("Warning", report.counts["warning"]),
            ("Info", report.counts["info"]),
            ("Unknown", report.counts["unknown"]),
        )
    )
    summary_table = Table(summary_rows, colWidths=[87 * mm, 87 * mm], repeatRows=1)
    summary_table.setStyle(table_style)
    story.extend([summary_table, _paragraph("Findings", heading)])
    if not report.findings:
        story.append(_paragraph("No findings.", body))
    for item in findings:
        story.extend(
            [
                _paragraph(f"[{item['severity']}] {item['rule_id']}", finding_heading),
                _paragraph(f"Tool: {item['tool']}", body),
                _paragraph(f"Location: {item['path']}:{item['start_line']}", body),
                _paragraph(f"ID: {item['id']}", body),
                _paragraph(f"Message: {item['message']}", body),
                _paragraph(f"Raw reference: {item['raw_reference']}", body),
            ]
        )
        if item.get("code"):
            story.append(_paragraph(item["code"], code))
        if item.get("metadata"):
            metadata = json.dumps(item["metadata"], ensure_ascii=False, sort_keys=True)
            story.append(_paragraph(f"Metadata: {metadata}", body))
        if analysis is not None:
            analysis_item = by_id.get(item["id"])
            if analysis_item:
                story.extend(
                    [
                        _paragraph(f"Classification: {analysis_item['label']}", body),
                        _paragraph(f"Changed: {analysis_item.get('diff_status', 'unknown')}", body),
                        _paragraph(f"Baseline: {analysis_item.get('baseline_status', 'unknown')}", body),
                    ]
                )
                if analysis_item.get("title"):
                    story.append(_paragraph(f"Title: {analysis_item['title']}", body))
                if analysis_item.get("cause"):
                    story.append(_paragraph(f"Cause: {analysis_item['cause']}", body))
                if analysis_item.get("impact"):
                    story.append(_paragraph(f"Impact: {analysis_item['impact']}", body))
                if analysis_item.get("remediation"):
                    story.append(_paragraph(f"Remediation: {analysis_item['remediation']}", body))
                if analysis_item.get("references"):
                    story.append(_paragraph(f"References: {', '.join(analysis_item['references'])}", body))
                evidence = evidence_summary(analysis_item.get("evidence"))
                if evidence:
                    story.append(_paragraph(f"Evidence: {evidence}", body))
        story.append(Spacer(1, 2 * mm))

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Security Report",
        author="CodeSec-Agent",
    )

    def add_page_number(canvas: object, doc: object) -> None:
        canvas.saveState()
        canvas.setFont(font, 8)
        canvas.drawCentredString(A4[0] / 2, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()

    try:
        document.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    except Exception as error:
        raise ReportRenderError("PDF rendering failed.") from error
    return buffer.getvalue()
