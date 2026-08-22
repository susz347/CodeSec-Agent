# CodeSec-Agent Project Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to run this roadmap one stage at a time. Each new subsystem requires its own approved design and implementation plan before code changes begin.

**Goal:** Deliver CodeSec-Agent as an evidence-first security-audit pipeline by completing independently verifiable subsystems locally, without GitHub publication unless separately approved.

**Architecture:** Scanner adapters emit one finding schema; analysis consumes findings and limited context; reporting consumes analysis; CI consumes completed local commands. The PR-Agent integration remains a verified separate review entry point.

**Tech Stack:** Python 3.12+, Semgrep, Bandit, npm audit, JSON, Markdown, GitHub Actions, DeepSeek through the existing PR-Agent configuration.

---

## Current status

| Capability | Status | Evidence |
| --- | --- | --- |
| GitHub Actions PR-Agent review | Complete | A closed validation PR produced an Action review. |
| Local PR-Agent CLI review | Complete | The same validation PR produced a local CLI review. |
| Validation-resource cleanup | Complete | The validation PR was not merged and its branch/worktree were deleted. |
| Semgrep design and detailed plan | Complete locally | `docs/superpowers/specs/2026-08-15-semgrep-phase3-design.md` and `docs/superpowers/plans/2026-08-15-semgrep-phase3.md`. |
| Semgrep implementation | Not started | No scanner code, tests, or scan artifacts exist. |
| Bandit, npm audit, analysis, reports, CI security scan | Not started | No implementation modules or workflow exist. |

## Execution rules

- Work in local branches/worktrees only; do not push, create a PR, or modify remote settings without separate authorization.
- Finish the active stage gate before starting the next dependent stage.
- Use one representative fixture set per parser, mocked external-process failure tests, and one real non-sensitive acceptance run per stage.
- Do not add coverage targets, repeat full scans for documentation edits, or compare LLM prose word-for-word.

### Task 1: Execute the existing Semgrep plan

**Plan:** `docs/superpowers/plans/2026-08-15-semgrep-phase3.md`

- [ ] **Step 1: Implement the approved Semgrep plan in its existing task order.**

- [ ] **Step 2: Run its required verification commands.**

```powershell
python -m unittest discover -s tests -v
.\.venv\Scripts\semgrep.exe --version
.\.venv\Scripts\python.exe -m scanner.run_semgrep --target . --artifacts artifacts
```

Expected: tests pass, Semgrep prints `1.163.0`, and raw plus normalized JSON exist.

- [ ] **Step 3: Verify the Semgrep stage gate.**

```powershell
.\.venv\Scripts\python.exe -c "import json; from pathlib import Path; raw=json.loads(Path('artifacts/semgrep-result.json').read_text(encoding='utf-8')); normalized=json.loads(Path('artifacts/findings.json').read_text(encoding='utf-8')); assert all(key in raw for key in ('results','errors','paths')); assert normalized['schema_version']=='1.0'; assert normalized['scan']['tool']=='semgrep'"
git check-ignore --quiet -- 'artifacts/semgrep-result.json'
```

Expected: every assertion passes and generated artifacts are ignored.

### Task 2: Create and execute the Bandit adapter plan

**Files to create after Task 1:** `docs/superpowers/specs/2026-08-22-bandit-adapter-design.md`, `docs/superpowers/plans/2026-08-22-bandit-adapter.md`, `scanner/normalize_bandit.py`, `tests/fixtures/bandit/`, `tests/test_normalize_bandit.py`.

- [ ] **Step 1: Design Bandit mapping to the existing schema.**

Map `test_id`, `issue_severity`, `filename`, `line_number`, `issue_text`, `code`, and `more_info` to finding fields. Unknown severity maps to `unknown`. The Bandit adapter must not change schema version `1.0`.

- [ ] **Step 2: Approve a separate detailed Bandit plan.**

The detailed plan must include normal, empty, and malformed fixtures; mocked command-runner errors; then one `bandit -r . -f json` acceptance run after fixture tests pass.

- [ ] **Step 3: Verify the Bandit stage gate.**

```powershell
python -m unittest discover -s tests -v
bandit -r . -f json -o artifacts/bandit-result.json
```

Expected: fixture tests pass and normalized output has schema `1.0` with tool `bandit`.

### Task 3: Create and execute the npm audit adapter plan

**Files to create after Task 2:** `docs/superpowers/specs/2026-08-22-npm-audit-adapter-design.md`, `docs/superpowers/plans/2026-08-22-npm-audit-adapter.md`, `scanner/normalize_npm_audit.py`, `tests/fixtures/npm-audit/`, `tests/test_normalize_npm_audit.py`.

- [ ] **Step 1: Confirm the target has `package.json`.**

Expected: if it does not, record npm audit as not applicable; do not synthesize an empty dependency scan.

- [ ] **Step 2: Design npm audit v2 mapping and approve its detailed plan.**

Map advisory identifier, severity, dependency path, affected range, advisory URL, and fix availability to the existing finding schema. The plan must include normal, no-vulnerability, and malformed fixtures, then one real `npm audit --json` run only for a target with dependencies.

- [ ] **Step 3: Verify the npm audit stage gate.**

```powershell
python -m unittest discover -s tests -v
npm audit --json
```

Expected: output uses schema `1.0` and tool `npm_audit`; a target without dependencies remains a documented not-applicable result.

### Task 4: Create and execute the security-analysis plan

**Files to create after Task 3:** `docs/superpowers/specs/2026-08-22-security-analysis-design.md`, `docs/superpowers/plans/2026-08-22-security-analysis.md`, `agent/security_reviewer.py`, `agent/prompts/security_review.md`, `tests/fixtures/findings/`, `tests/test_security_reviewer.py`.

- [ ] **Step 1: Design bounded inputs and outputs.**

Inputs are unified findings, an explicit code-context budget, and a local CWE/OWASP reference subset. Each output item uses `confirmed`, `suspicious`, or `possible_false_positive`, cites a finding ID, and gives defensive remediation without exploitation steps.

- [ ] **Step 2: Approve a detailed analysis plan.**

It must test JSON/Markdown structure and finding IDs with fixtures, not exact natural-language wording. A real model call happens once with non-sensitive content only after separate authorization.

- [ ] **Step 3: Verify the analysis stage gate.**

```powershell
python -m unittest tests.test_security_reviewer -v
```

Expected: all labels are valid and every analysis item references an existing finding ID.

### Task 5: Create and execute the Markdown-report plan

**Files to create after Task 4:** `docs/superpowers/specs/2026-08-22-markdown-report-design.md`, `docs/superpowers/plans/2026-08-22-markdown-report.md`, `report/generate_markdown.py`, `tests/test_generate_markdown.py`, `examples/security-report.md`.

- [ ] **Step 1: Design a deterministic report contract.**

Render scan metadata, severity counts, finding evidence, labels, impact, remediation, and references. The report consumes findings plus analysis only; it does not run a scanner or model.

- [ ] **Step 2: Approve a detailed report plan.**

It must cover empty, one-finding, and multi-tool fixtures and verify headings plus finding IDs rather than prose snapshots.

- [ ] **Step 3: Verify the report stage gate.**

```powershell
python -m unittest tests.test_generate_markdown -v
```

Expected: the three fixture classes produce readable Markdown and the example contains no credentials or production data.

### Task 6: Create and execute the CI/PR integration plan

**Files to create after Task 5:** `docs/superpowers/specs/2026-08-22-security-ci-design.md`, `docs/superpowers/plans/2026-08-22-security-ci.md`, `.github/workflows/security-scan.yml`.

- [ ] **Step 1: Design CI security boundaries.**

Run only completed local commands; use `contents: read` and `pull-requests: write`; do not use `pull_request_target`; skip Forks and Bots; save artifacts; and publish a summary without full source or credentials.

- [ ] **Step 2: Approve a detailed CI plan.**

It must include YAML static checks, local artifact-shape tests, and one same-repository non-sensitive PR validation. Initial policy reports findings and never blocks merging.

- [ ] **Step 3: Verify the CI stage gate.**

```powershell
git diff --check
```

Expected: workflow review confirms least privilege; an Action stores artifacts; and the summary includes only counts, rule IDs, paths, and artifact links.

### Task 7: Evaluate optional enhancements after CI is stable

- [ ] **Step 1: Select one observed gap from local CWE/OWASP knowledge, false-positive feedback, multi-language policy, RAG, Word/PDF export, or visualization.**

Expected: selection states the observed gap, intended user, available inputs, and why it outranks the alternatives.

- [ ] **Step 2: Start a new design-to-plan cycle for that one enhancement.**

Expected: it does not change completed finding schema semantics without an explicit version decision.

## Stop conditions

- Stop and diagnose the current stage if its contract test or real acceptance run fails.
- Stop before live DeepSeek calls, GitHub secrets, pushes, PR creation, or merge-blocking policies until separately authorized.
- Stop before Bandit or npm audit work until the Semgrep stage gate passes.
