# Phase 4 Multiformat Reports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the local security report CLI to generate validated XLSX, DOCX, and PDF files from the existing `SecurityReport` model while preserving JSON/Markdown compatibility.

**Architecture:** Three focused renderers return bytes and never read scanner files. The Python CLI resolves selected formats, renders all outputs before writing, and commits the selected file group with backup-based rollback; a small JavaScript process owns only DOCX OOXML generation.

**Tech Stack:** Python 3.12, openpyxl 3.1.5, ReportLab 4.4.9, pypdf 6.10.0 for tests, Node.js, docx 9.6.1, unittest.

---

### Task 1: Pin report dependencies and define renderer errors

**Files:**
- Create: `requirements-reporting.txt`
- Create: `package.json`
- Create: `reporting/errors.py`
- Modify: `requirements-dev.txt`
- Generate: `package-lock.json`

- [ ] **Step 1: Add exact Python and Node dependency declarations**

```text
# requirements-reporting.txt
openpyxl==3.1.5
reportlab==4.4.9
```

```json
{"private":true,"dependencies":{"docx":"9.6.1"}}
```

Add `-r requirements-reporting.txt` and `pypdf==6.10.0` to `requirements-dev.txt`.

- [ ] **Step 2: Add one shared rendering exception**

```python
class ReportRenderError(RuntimeError):
    """Raised when an optional report format cannot be rendered."""
```

- [ ] **Step 3: Install locked dependencies without running package scripts**

Run: `\.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt` and `npm install --ignore-scripts`.
Expected: both commands exit 0 and `package-lock.json` locks `docx` 9.6.1.

- [ ] **Step 4: Commit dependency declarations**

```powershell
git add requirements-dev.txt requirements-reporting.txt package.json package-lock.json reporting/errors.py
git commit -m "build: add multiformat report dependencies"
```

### Task 2: Render Excel workbooks

**Files:**
- Create: `reporting/render_excel.py`
- Create: `tests/test_render_excel.py`

- [ ] **Step 1: Write a failing workbook contract test**

```python
def test_excel_contains_summary_sources_and_findings(self) -> None:
    workbook = load_workbook(BytesIO(render_excel(self.report)), data_only=False)
    self.assertEqual(workbook.sheetnames, ["Summary", "Sources", "Findings"])
    self.assertEqual(workbook["Summary"]["B3"].value, 1)
    self.assertEqual(workbook["Findings"]["A2"].value, "id")
```

- [ ] **Step 2: Run the focused test and confirm the renderer import is missing**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_render_excel -v`
Expected: ERROR with `ModuleNotFoundError: reporting.render_excel`.

- [ ] **Step 3: Implement `render_excel(report) -> bytes`**

Create three worksheets in fixed order, populate report values, apply Arial font, dark-blue headers, frozen finding headers, filters, sensible column widths, and severity fills. Save the workbook to `BytesIO` and return its bytes; do not add formulas because the workbook serializes an already-calculated immutable report.

- [ ] **Step 4: Run focused and complete tests**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_render_excel -v` then `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
Expected: all tests pass without warnings.

- [ ] **Step 5: Commit the Excel renderer**

```powershell
git add reporting/render_excel.py tests/test_render_excel.py
git commit -m "feat: render Excel security reports"
```

### Task 3: Render DOCX documents

**Files:**
- Create: `reporting/render_docx.js`
- Create: `reporting/render_docx.py`
- Create: `tests/test_render_docx.py`

- [ ] **Step 1: Write a failing OOXML content test**

```python
def test_docx_contains_report_sections(self) -> None:
    payload = render_docx(self.report)
    with ZipFile(BytesIO(payload)) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    for text in ("Security Report", "Scan Sources", "Summary", "rule", "Avoid exec"):
        self.assertIn(text, document)
```

- [ ] **Step 2: Run the focused test and confirm the wrapper import is missing**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_render_docx -v`
Expected: ERROR with `ModuleNotFoundError: reporting.render_docx`.

- [ ] **Step 3: Implement the Python wrapper and docx-js renderer**

`render_docx(report) -> bytes` serializes `report_dict(report)` to UTF-8 stdin, resolves `CODESEC_NODE` or `node`, invokes `reporting/render_docx.js`, and raises `ReportRenderError` using stderr without logging report content. The JavaScript renderer reads stdin, creates an explicit A4 document with Arial styles, fixed-DXA tables, `ShadingType.CLEAR`, finding headings, code paragraphs, and a page-number footer, then writes `Packer.toBuffer(document)` to stdout.

- [ ] **Step 4: Run focused and complete tests**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_render_docx -v` then the complete unittest suite.
Expected: all tests pass and the returned bytes are a valid ZIP-based DOCX.

- [ ] **Step 5: Commit the DOCX renderer**

```powershell
git add reporting/render_docx.js reporting/render_docx.py tests/test_render_docx.py
git commit -m "feat: render DOCX security reports"
```

### Task 4: Render PDF documents

**Files:**
- Create: `reporting/render_pdf.py`
- Create: `tests/test_render_pdf.py`

- [ ] **Step 1: Write a failing PDF structure and text test**

```python
def test_pdf_contains_report_sections(self) -> None:
    reader = PdfReader(BytesIO(render_pdf(self.report)))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    self.assertGreaterEqual(len(reader.pages), 1)
    for value in ("Security Report", "Scan Sources", "Summary", "Avoid exec"):
        self.assertIn(value, text)
```

- [ ] **Step 2: Run the focused test and confirm the renderer import is missing**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_render_pdf -v`
Expected: ERROR with `ModuleNotFoundError: reporting.render_pdf`.

- [ ] **Step 3: Implement `render_pdf(report) -> bytes`**

Register `CODESEC_REPORT_FONT` or the first valid Microsoft YaHei, Noto Sans CJK, or DejaVu Sans candidate. Build an A4 Platypus document in `BytesIO` with escaped paragraphs, source and severity tables, finding headings, messages, locations, code, metadata, and `No findings.` for an empty report. Raise `ReportRenderError` if no usable font exists.

- [ ] **Step 4: Run focused and complete tests**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_render_pdf -v` then the complete unittest suite.
Expected: all tests pass; pypdf parses at least one page and the expected text.

- [ ] **Step 5: Commit the PDF renderer**

```powershell
git add reporting/render_pdf.py tests/test_render_pdf.py
git commit -m "feat: render PDF security reports"
```

### Task 5: Select formats and atomically commit an output group

**Files:**
- Modify: `reporting/cli.py`
- Modify: `tests/test_reporting_cli.py`

- [ ] **Step 1: Write failing CLI tests for compatibility, all formats, and rollback**

```python
def test_all_format_generates_five_reports(self) -> None:
    result = main(["--input", str(source), "--output-dir", str(output), "--format", "all"])
    self.assertEqual(result, 0)
    self.assertEqual({p.suffix for p in output.glob("security-report.*")}, {".json", ".md", ".xlsx", ".docx", ".pdf"})
```

Extend the existing injected replacement failure test to select all formats and assert every previous report is restored.

- [ ] **Step 2: Run CLI tests and confirm `--format` is rejected**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_reporting_cli -v`
Expected: FAIL because argparse does not recognize `--format`.

- [ ] **Step 3: Generalize rendering and transactional commit**

Parse repeatable `--format` choices with default `json,markdown`; expand `all` to the fixed order. Render every selected format to bytes before creating temporary files. Replace `_commit_report_pair` with `_commit_outputs(pairs)` using the existing backup/rollback algorithm for an arbitrary selected output group. Catch `ReportRenderError` together with input and filesystem errors.

- [ ] **Step 4: Run CLI and complete test suites**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_reporting_cli -v` and then the complete unittest suite.
Expected: all tests pass and default JSON/Markdown behavior remains unchanged.

- [ ] **Step 5: Commit the CLI extension**

```powershell
git add reporting/cli.py tests/test_reporting_cli.py
git commit -m "feat: generate selected report formats"
```

### Task 6: Document and perform real multiformat acceptance

**Files:**
- Modify: `docs/deployment-steps.md`
- Modify: `docs/project-checklist.md`
- Modify: `docs/roadmap.md`
- Modify: `docs/superpowers/plans/2026-08-22-phase4-multiformat-reports.md`

- [ ] **Step 1: Document dependency installation and `--format all`**

Show the exact install and report commands, state the no-network runtime boundary, list five ignored artifacts, and leave Agent analysis and automation unchecked.

- [ ] **Step 2: Run the full automated verification**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`, `npm audit --audit-level=high`, and `git diff --check`.
Expected: all tests pass, npm reports no high-severity vulnerability, and the diff check is clean.

- [ ] **Step 3: Generate and structurally validate five real reports**

Run the CLI with `artifacts/findings.json`, `artifacts/bandit-findings.json`, `artifacts/npm-audit-findings.json`, `--format all`, and `--output-dir artifacts`. Parse JSON, Markdown, XLSX, DOCX, and PDF; assert three sources and matching finding totals.

- [ ] **Step 4: Render XLSX, DOCX, and PDF for visual inspection**

Use LibreOffice headless conversion for XLSX/DOCX previews and Poppler for PDF page images. Inspect title, tables, wrapping, page boundaries, and absence of clipped or overlapping content.

- [ ] **Step 5: Commit documentation and acceptance instructions**

```powershell
git add docs/deployment-steps.md docs/project-checklist.md docs/roadmap.md docs/superpowers/plans/2026-08-22-phase4-multiformat-reports.md
git commit -m "docs: complete multiformat report delivery"
```
