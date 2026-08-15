# Semgrep Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Semgrep-only local scan pipeline that stores raw JSON and a versioned normalized finding document.

**Architecture:** `scanner.models` defines the stable contract; `scanner.normalize_semgrep` is a pure JSON adapter; `scanner.run_semgrep` is the only subprocess owner. Fixtures make all unit tests offline; the final task is the only real Semgrep invocation.

**Tech Stack:** Python 3.12+, standard-library `unittest`, Semgrep CLI 1.163.0, JSON, PowerShell.

---

## File map

- Modify: `.gitignore`, `docs/roadmap.md`, `docs/project-checklist.md`, `docs/deployment-steps.md`.
- Create: `requirements-dev.txt`, `scanner/__init__.py`, `scanner/models.py`, `scanner/normalize_semgrep.py`, `scanner/run_semgrep.py`.
- Create: `tests/__init__.py`, `tests/test_models.py`, `tests/test_normalize_semgrep.py`, `tests/test_run_semgrep.py`, `tests/fixtures/semgrep/empty.json`, `tests/fixtures/semgrep/findings.json`, `tests/fixtures/semgrep/missing-required-field.json`.

### Task 1: Pin Semgrep and protect generated artifacts

**Files:** Modify `.gitignore`; create `requirements-dev.txt`.

- [ ] **Step 1: Add the failing precondition checks**

```powershell
if (Test-Path -LiteralPath 'requirements-dev.txt') { throw 'requirements-dev.txt must not exist before this task' }
git check-ignore --quiet -- 'artifacts/semgrep-result.json'
if ($LASTEXITCODE -eq 0) { throw 'artifacts are already ignored unexpectedly' }
```

Expected: the first assertion succeeds and `git check-ignore` exits nonzero.

- [ ] **Step 2: Create the exact configuration**

Append this exact block to `.gitignore`:

```gitignore
# Local static-analysis artifacts
/artifacts/
```

Create `requirements-dev.txt` with exactly `semgrep==1.163.0` followed by one newline.

- [ ] **Step 3: Verify and commit**

```powershell
git check-ignore --quiet -- 'artifacts/semgrep-result.json'
if ($LASTEXITCODE -ne 0) { throw 'artifacts are not ignored' }
git add -- '.gitignore' 'requirements-dev.txt'
git diff --cached --check
git commit -m 'chore: add Semgrep development dependency'
```

Expected: the commit contains only `.gitignore` and `requirements-dev.txt`.

### Task 2: Define the normalized finding contract

**Files:** Create `scanner/__init__.py`, `scanner/models.py`, `tests/__init__.py`, `tests/test_models.py`.

- [ ] **Step 1: Write a failing contract test**

Create `tests/test_models.py`:

```python
import unittest
from scanner.models import Finding, ScanDocument

class ModelsTests(unittest.TestCase):
    def test_unknown_severity_is_retained(self):
        finding = Finding.create("rule", "CRITICAL", "example.py", 3, 1, 3, 16,
                                 "Avoid exec.", "exec(user_input)", {}, "/results/0")
        self.assertEqual(finding.severity, "unknown")
        self.assertEqual(finding.metadata["semgrep_severity"], "CRITICAL")
        self.assertEqual(len(finding.id), 16)

    def test_document_has_fixed_scan_metadata(self):
        document = ScanDocument.create("1.163.0", ".", [])
        self.assertEqual(document.to_dict()["schema_version"], "1.0")
        self.assertEqual(document.to_dict()["scan"]["ruleset"], "p/security-audit")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Confirm the test fails**

Run: `python -m unittest tests.test_models -v`

Expected: `ModuleNotFoundError: No module named 'scanner'`.

- [ ] **Step 3: Implement the contract**

Create empty package markers. Implement frozen `Finding` and `ScanDocument` dataclasses in `scanner/models.py`. `Finding.create(rule_id, severity, path, start_line, start_column, end_line, end_column, message, code, metadata, raw_reference)` must calculate the first 16 SHA-256 characters over `semgrep|rule_id|path|start_line|start_column`; accept case-insensitive `error`, `warning`, and `info`; map all others to `unknown` and retain the original value in `metadata["semgrep_severity"]`. `to_dict` must emit every field from the approved design. `ScanDocument.create(tool_version, target, findings)` must emit schema version `1.0`, tool `semgrep`, ruleset `p/security-audit`, target, UTC ISO-8601 timestamp, and findings.

- [ ] **Step 4: Verify and commit**

```powershell
python -m unittest tests.test_models -v
git add -- 'scanner/__init__.py' 'scanner/models.py' 'tests/__init__.py' 'tests/test_models.py'
git diff --cached --check
git commit -m 'feat: define normalized security finding contract'
```

Expected: both model tests pass.

### Task 3: Normalize Semgrep JSON with offline fixtures

**Files:** Create `scanner/normalize_semgrep.py`, three fixtures, `tests/test_normalize_semgrep.py`.

- [ ] **Step 1: Write failing adapter tests**

Test `normalize_semgrep(payload, "1.163.0", ".")` against fixtures. Assert empty results stay empty; a complete finding maps `check_id` to `rule_id`, has `path == "example.py"`, `start_line == 3`, metadata `cwe == ["CWE-78"]`, and `raw_reference == "/results/0"`; absent top-level `paths` raises `SemgrepFormatError` mentioning `/paths`; missing `extra.message` raises `SemgrepFormatError` mentioning `/results/0/extra/message`.

- [ ] **Step 2: Confirm failure**

Run: `python -m unittest tests.test_normalize_semgrep -v`

Expected: import failure for `scanner.normalize_semgrep`.

- [ ] **Step 3: Add non-sensitive fixtures**

Create `empty.json` exactly as:

```json
{"version":"1.163.0","results":[],"errors":[],"paths":{"scanned":[],"skipped":[]}}
```

Create `findings.json` exactly as:

```json
{"version":"1.163.0","results":[{"check_id":"python.lang.security.audit.exec-used","path":"example.py","start":{"line":3,"col":1},"end":{"line":3,"col":16},"extra":{"message":"Avoid exec.","severity":"WARNING","lines":"exec(user_input)","metadata":{"cwe":["CWE-78"],"owasp":["A03:2021 - Injection"]}}}],"errors":[],"paths":{"scanned":["example.py"],"skipped":[]}}
```

Create `missing-required-field.json` exactly as:

```json
{"version":"1.163.0","results":[{"check_id":"rule","path":"example.py","start":{"line":1,"col":1},"end":{"line":1,"col":2},"extra":{"severity":"INFO"}}],"errors":[]}
```

- [ ] **Step 4: Implement and verify the adapter**

Define `SemgrepFormatError(ValueError)` and `normalize_semgrep(payload, tool_version, target)`. Require `results`, `errors`, and `paths`; require every result to have `check_id`, `path`, `start.line`, `end.line`, and `extra.message`; copy only `cwe`, `owasp`, `category`, `technology`, and `references` from metadata; use `Finding.create`; and never read source files or experimental fields.

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass with network disabled.

- [ ] **Step 5: Commit**

```powershell
git add -- 'scanner/normalize_semgrep.py' 'tests/fixtures/semgrep' 'tests/test_normalize_semgrep.py'
git diff --cached --check
git commit -m 'feat: normalize Semgrep JSON findings'
```

### Task 4: Run Semgrep and write artifacts

**Files:** Create `scanner/run_semgrep.py`, `tests/test_run_semgrep.py`.

- [ ] **Step 1: Write failing runner tests**

Mock `subprocess.run` and assert that `run_scan(Path('.'), Path('artifacts'))` invokes exactly `['semgrep', 'scan', '--config', 'p/security-audit', '--json', '--output', 'artifacts/semgrep-result.json', '.']`; result codes 0 and 1 are accepted only if parseable raw JSON exists; `findings.json` is written; return code 2 and missing raw output raise `SemgrepRunError`.

- [ ] **Step 2: Confirm failure**

Run: `python -m unittest tests.test_run_semgrep -v`

Expected: import failure for `scanner.run_semgrep`.

- [ ] **Step 3: Implement runner behavior**

Implement `SemgrepRunError(RuntimeError)`, `run_scan(target: Path, artifacts: Path) -> Path`, and `main() -> int`. Remove only `semgrep-result.json` and `findings.json` before execution; call `subprocess.run` with text capture and `check=False`; accept only result codes 0 or 1 with raw JSON; call `normalize_semgrep`; write normalized JSON as UTF-8 with indentation and trailing newline. Leave any new raw JSON after an error but never create partial normalized output. `main` accepts `--target` default `.` and `--artifacts` default `artifacts`, prints the result path on success, and writes only the exception message to stderr on failure.

- [ ] **Step 4: Verify and commit**

```powershell
python -m unittest discover -s tests -v
git add -- 'scanner/run_semgrep.py' 'tests/test_run_semgrep.py'
git diff --cached --check
git commit -m 'feat: run local Semgrep scans'
```

### Task 5: Document and validate the Semgrep-first milestone

**Files:** Modify `docs/roadmap.md`, `docs/project-checklist.md`, `docs/deployment-steps.md`.

- [ ] **Step 1: Update documentation**

Document Semgrep scan plus normalization as the immediate Phase 3 deliverable. Keep Bandit and npm audit unchecked and explicitly deferred pending validation. Add this exact command to `docs/deployment-steps.md`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m scanner.run_semgrep --target . --artifacts artifacts
Get-Content -LiteralPath 'artifacts\findings.json' -Raw | ConvertFrom-Json | ConvertTo-Json -Depth 8
```

State that `artifacts/` is ignored, registry rules need network access, findings do not block merges, and Phase 3 neither calls DeepSeek nor comments on PRs.

- [ ] **Step 2: Run the real acceptance scan**

```powershell
python -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\semgrep.exe --version
.\.venv\Scripts\python.exe -m scanner.run_semgrep --target . --artifacts artifacts
```

Expected: unit tests pass, the version is `1.163.0`, and both artifact files exist.

- [ ] **Step 3: Validate output and commit docs**

```powershell
.\.venv\Scripts\python.exe -c "import json; from pathlib import Path; raw=json.loads(Path('artifacts/semgrep-result.json').read_text(encoding='utf-8')); normalized=json.loads(Path('artifacts/findings.json').read_text(encoding='utf-8')); assert all(key in raw for key in ('results','errors','paths')); assert normalized['schema_version']=='1.0'; assert normalized['scan']['tool']=='semgrep'; print(len(normalized['findings']))"
git check-ignore --quiet -- 'artifacts/semgrep-result.json'
git status --short
git add -- 'docs/roadmap.md' 'docs/project-checklist.md' 'docs/deployment-steps.md'
git diff --cached --check
git commit -m 'docs: document Semgrep scanning workflow'
```

Expected: a finding count prints, artifacts remain absent from status, and the documentation-only commit excludes artifacts.

## Completion evidence

- `python -m unittest discover -s tests -v` passes offline.
- Semgrep prints `1.163.0`.
- The real scan creates parseable raw JSON with `results`, `errors`, and `paths`, plus normalized schema `1.0` output.
- Generated artifacts are ignored.
- No Bandit, npm audit, GitHub Action, PR comment, DeepSeek, report, or merge-blocking behavior is introduced.
