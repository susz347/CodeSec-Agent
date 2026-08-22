# Phase 3 Bandit and npm audit Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax.

Goal: Complete Phase 3 by adding Bandit and npm audit adapters that emit the existing normalized finding schema.

Architecture: Generalize the model without changing Semgrep output. Each tool has a pure JSON normalizer, a subprocess-owning runner, offline fixtures, mock runner tests, and one real validation.

Tech Stack: Python 3.12+, standard-library unittest, Bandit 1.9.4, npm CLI, JSON, PowerShell.

---

## File map

- Modify: requirements-dev.txt, scanner/models.py, tests/test_models.py, docs/roadmap.md, docs/project-checklist.md, docs/deployment-steps.md.
- Create: scanner/normalize_bandit.py, scanner/run_bandit.py, scanner/normalize_npm_audit.py, scanner/run_npm_audit.py.
- Create: offline fixtures and tests/test_normalize_*.py / tests/test_run_*.py for both tools.

### Task 1: Generalize the contract and pin Bandit

Files: Modify scanner/models.py, tests/test_models.py, requirements-dev.txt.

- [ ] Step 1: Write failing compatibility tests

Add this test while retaining the Semgrep stability test:

~~~
def test_identifier_includes_tool(self) -> None:
    shared = dict(rule_id="B101", severity="info", path="example.py",
                  start_line=1, start_column=None, end_line=1,
                  end_column=None, message="x", code=None,
                  metadata={}, raw_reference="/results/0")
    self.assertNotEqual(
        Finding.create(tool="semgrep", **shared).id,
        Finding.create(tool="bandit", **shared).id,
    )
~~~

- [ ] Step 2: Confirm red

Run: .\.venv\Scripts\python.exe -m unittest tests.test_models -v
Expected: TypeError because Finding.create does not accept tool.

- [ ] Step 3: Implement the minimal compatible change

Make Finding.create(..., *, tool="semgrep") calculate the ID over tool|rule_id|path|start_line|start_column. Make ScanDocument.create(..., *, tool="semgrep", ruleset="p/security-audit") use those scan values. Append exactly bandit==1.9.4 to requirements-dev.txt. Existing Semgrep calls must pass tool="semgrep" explicitly and retain their prior output.

- [ ] Step 4: Verify and commit

~~~
.\.venv\Scripts\python.exe -m unittest tests.test_models -v
git add -- scanner/models.py tests/test_models.py requirements-dev.txt
git diff --cached --check
git commit -m "feat: generalize finding model for scanners"
~~~

### Task 2: Normalize and run Bandit

Files: Create scanner/normalize_bandit.py, scanner/run_bandit.py, tests/fixtures/bandit/, tests/test_normalize_bandit.py, tests/test_run_bandit.py.

- [ ] Step 1: Write failing normalizer tests and fixtures

Use a finding with test_id B101, filename example.py, line_number 1, line_range [1], issue_severity MEDIUM, issue_text, code, and more_info. Test empty results; MEDIUM -> warning; HIGH -> error; LOW -> info; /results/0 pointer; missing /errors; missing /results/0/issue_text; and reference metadata.

- [ ] Step 2: Confirm red, then implement

Run: .\.venv\Scripts\python.exe -m unittest tests.test_normalize_bandit -v.
Implement BanditFormatError and normalize_bandit(payload, tool_version, target). Require top-level results and errors; map test_id, relative filename, line range, text, code, and more_info; never invoke Bandit or read sources.

- [ ] Step 3: Write failing runner tests, then implement

Mock subprocess.run and assert the exact command:

~~~
["bandit", "-r", ".", "-f", "json", "-o", raw_output.as_posix()]
~~~

Accept only exit codes 0/1 with parseable raw JSON. Reject code 2, missing raw output, invalid JSON, and missing executable. Implement BanditRunError, run_scan, and main; write bandit-result.json and bandit-findings.json; use tool version 1.9.4 and ruleset bandit-default.

- [ ] Step 4: Verify, real-scan, and commit

~~~
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\bandit.exe --version
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m scanner.run_bandit --target scanner --artifacts artifacts
git add -- scanner/normalize_bandit.py scanner/run_bandit.py tests/fixtures/bandit tests/test_normalize_bandit.py tests/test_run_bandit.py
git diff --cached --check
git commit -m "feat: add local Bandit scanning"
~~~

Expected: both Bandit artifacts parse; output is schema 1.0, tool bandit, version 1.9.4; artifacts are ignored.

### Task 3: Normalize npm audit JSON

Files: Create scanner/normalize_npm_audit.py, tests/fixtures/npm-audit/, tests/test_normalize_npm_audit.py.

- [ ] Step 1: Write failing tests and fixtures

Provide a vulnerabilities.lodash object with name, severity high, range, and a via object containing title, url, and cwe; include top-level metadata. Assert rule_id npm-audit/lodash, severity error, path package-lock.json, line 1, category dependency, URL/CWE metadata, and /vulnerabilities/lodash. Also test empty vulnerabilities, missing /metadata, and absent /vulnerabilities/lodash/range.

- [ ] Step 2: Confirm red, then implement

Run: .\.venv\Scripts\python.exe -m unittest tests.test_normalize_npm_audit -v.
Implement NpmAuditFormatError and normalize_npm_audit(payload, tool_version, target). Require vulnerabilities and metadata; create one finding per vulnerability key; map critical/high to error, moderate to warning, low/info to info; JSON-pointer escape keys; collect only CWE and URL references from via.

- [ ] Step 3: Verify and commit

~~~
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git add -- scanner/normalize_npm_audit.py tests/fixtures/npm-audit tests/test_normalize_npm_audit.py
git diff --cached --check
git commit -m "feat: normalize npm audit findings"
~~~

### Task 4: Run npm audit safely

Files: Create scanner/run_npm_audit.py, tests/test_run_npm_audit.py, tests/fixtures/npm-project/package.json, tests/fixtures/npm-project/package-lock.json.

- [ ] Step 1: Write failing runner tests

Mock npm --version and npm audit --json --package-lock-only --ignore-scripts. Assert raw stdout becomes npm-audit-result.json; code 0/1 with JSON writes normalized output; no package-lock.json raises NpmAuditNotApplicable; code 2 or non-JSON stdout raises NpmAuditRunError without normalized output.

- [ ] Step 2: Confirm red, then implement

Run: .\.venv\Scripts\python.exe -m unittest tests.test_run_npm_audit -v.
Implement the two exceptions, run_scan, and main. Require a target-local lockfile, do not run npm install or npm audit fix, capture UTF-8 safely, and record npm --version in scan metadata.

- [ ] Step 3: Add the minimal real fixture and verify

Create package.json:

~~~
{"name":"npm-audit-fixture","version":"1.0.0","private":true}
~~~

Create package-lock.json:

~~~
{"name":"npm-audit-fixture","version":"1.0.0","lockfileVersion":3,"requires":true,"packages":{"":{"name":"npm-audit-fixture","version":"1.0.0"}}}
~~~

Then run:

~~~
npm --version
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m scanner.run_npm_audit --target tests/fixtures/npm-project --artifacts artifacts
~~~

Assert both npm artifacts parse, schema is 1.0, tool is npm-audit, tool version is nonempty, and artifacts are ignored.

- [ ] Step 4: Commit

~~~
git add -- scanner/run_npm_audit.py tests/test_run_npm_audit.py tests/fixtures/npm-project
git diff --cached --check
git commit -m "feat: run local npm audit scans"
~~~

### Task 5: Complete Phase 3 documentation and final acceptance

Files: Modify docs/roadmap.md, docs/project-checklist.md, docs/deployment-steps.md.

- [ ] Step 1: Document the final workflow

Document Bandit 1.9.4, the three scan commands, all six artifact files, npm lockfile prerequisite, safe flags, ignored artifacts, and that Phase 4 remains unimplemented.

- [ ] Step 2: Run the final evidence set

~~~
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m scanner.run_semgrep --target . --artifacts artifacts
.\.venv\Scripts\python.exe -m scanner.run_bandit --target scanner --artifacts artifacts
.\.venv\Scripts\python.exe -m scanner.run_npm_audit --target tests/fixtures/npm-project --artifacts artifacts
git check-ignore --quiet -- artifacts/semgrep-result.json
git check-ignore --quiet -- artifacts/bandit-result.json
git check-ignore --quiet -- artifacts/npm-audit-result.json
git status --short
~~~

Expected: all tests pass; all six JSON artifacts parse; no artifact is in status; no scan invokes DeepSeek, writes a PR comment, or modifies dependencies.

- [ ] Step 3: Commit

~~~
git add -- docs/roadmap.md docs/project-checklist.md docs/deployment-steps.md
git diff --cached --check
git commit -m "docs: complete local scan workflow"
~~~
