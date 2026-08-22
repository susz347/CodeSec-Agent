# Phase 4 Local Reports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax.

**Goal:** Merge schema 1.0 scanner finding documents and emit deterministic JSON and Markdown security reports.

**Architecture:** reporting.load_findings validates raw documents and builds an immutable SecurityReport from reporting.models. Dedicated renderers serialize that model; reporting.cli atomically writes both outputs and owns no scanner, model, or GitHub integration.

**Tech Stack:** Python 3.12+, dataclasses, json, argparse, unittest.

---

### Task 1: Report model and loader

**Files:** Create reporting/__init__.py, reporting/models.py, reporting/load_findings.py, tests/test_reporting_models.py.

- [ ] Write tests asserting multi-source merge, severity counts, stable error/warning/info/unknown ordering, and rejection of schema != 1.0 or non-object findings.
- [ ] Run .\.venv\Scripts\python.exe -m unittest tests.test_reporting_models -v and confirm missing reporting modules.
- [ ] Implement ScanSource and SecurityReport frozen dataclasses plus load_documents(paths). Copy input dictionaries, validate required fields, calculate counts, and sort by severity/tool/path/start_line/id.
- [ ] Run the focused and complete unittest suites.
- [ ] Commit as feat: build normalized security reports.

### Task 2: JSON and Markdown renderers

**Files:** Create reporting/render_json.py, reporting/render_markdown.py, tests/test_report_renderers.py.

- [ ] Write tests for deterministic JSON keys and Markdown title, source table, severity table, finding location, message, code fence, metadata, and empty report.
- [ ] Run tests and confirm missing renderer imports.
- [ ] Implement render_json(report) with UTF-8-friendly indentation and trailing newline; implement render_markdown(report) without reading files.
- [ ] Run focused and complete tests.
- [ ] Commit as feat: render JSON and Markdown security reports.

### Task 3: Atomic report CLI

**Files:** Create reporting/cli.py, tests/test_reporting_cli.py.

- [ ] Write tests for repeated --input, --output-dir, successful dual outputs, invalid input, and absence of partial files after failure.
- [ ] Run tests and confirm missing CLI module.
- [ ] Implement main(argv), write temporary sibling files, then replace security-report.json and security-report.md only after both render successfully.
- [ ] Run focused and complete tests.
- [ ] Commit as feat: add local security report CLI.

### Task 4: Documentation and real acceptance

**Files:** Modify .gitignore, docs/roadmap.md, docs/project-checklist.md, docs/deployment-steps.md.

- [ ] Ensure /artifacts/ already ignores report files; document the repeated --input command and Phase 4 first-slice boundary.
- [ ] Run all tests.
- [ ] Run the CLI with artifacts/semgrep-findings.json, artifacts/bandit-findings.json, and artifacts/npm-audit-findings.json when present; otherwise generate equivalent current scanner outputs first.
- [ ] Parse security-report.json, inspect required Markdown sections, confirm report artifacts are ignored, and confirm Git status contains only intended sources/docs/tests.
- [ ] Commit as docs: document local security reports.

