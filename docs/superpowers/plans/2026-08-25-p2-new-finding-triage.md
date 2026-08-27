# P2 New-Finding Triage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow operators to persist a human disposition for a new finding from a real PR without changing baseline semantics or retaining sensitive finding content.

**Architecture:** `agent.triage_cli` resolves a selected normalized finding from an existing schema 1.0 JSON input, calculates its stable fingerprint, and passes only that finding's identity to `agent.triage.add_disposition`. The triage layer accepts that identity only when a trusted normalized finding was supplied; it keeps dispositions deduplicated by fingerprint and stores no path, code, message, evidence, PR, or artifact reference. Existing fingerprint-only baseline dispositions remain compatible.

**Tech Stack:** Python 3.12 standard library, existing `agent.triage`, `agent.triage_cli`, unittest, Markdown.

---

## File structure

| File | Responsibility |
| --- | --- |
| `agent/triage.py` | Permit a non-baseline disposition only when the caller supplies normalized finding identity. |
| `agent/triage_cli.py` | Add mutually exclusive `--fingerprint` and `--input` + `--finding-id` disposition selection. |
| `tests/test_triage.py` | Prove new finding persistence, CLI lookup failures, statistics, and replacement semantics. |
| `docs/trial-phase-2.md` | Show the safe real-PR command that selects a finding from local scanner output. |
| `docs/trial-phase-2-log.md` | Record rule IDs per PR and complete the de-identified false-negative seed fields. |

### Task 1: Specify failing triage tests

**Files:**
- Modify: `tests/test_triage.py`

- [x] **Step 1: Add a unit test for a new finding disposition**

Add a second finding with different code, build a baseline containing only the first finding, then assert this call succeeds and persists only safe identity fields:

```python
updated = add_disposition(
    build_baseline([baseline_finding]),
    fingerprint=fingerprint(new_finding),
    finding=new_finding,
    resolution="true_positive",
    reviewer="alice",
    machine_label="confirmed",
    note="Validated without storing source evidence.",
)
self.assertEqual(updated["dispositions"][0]["tool"], "semgrep")
self.assertEqual(updated["dispositions"][0]["rule_id"], "python.lang.security.audit.exec-used")
self.assertNotIn("path", updated["dispositions"][0])
self.assertNotIn("code", updated["dispositions"][0])
```

- [x] **Step 2: Add CLI tests for selection and clean failure**

Write a normalized findings document with a non-baseline `f-new` finding. Invoke `disposition --input <file> --finding-id f-new` and assert the persisted disposition is grouped by rule. Invoke the same command with `--finding-id missing` and assert it returns `1` without adding a disposition.

- [x] **Step 3: Run the focused test before implementation**

Run: `python -m unittest tests.test_triage -v`

Expected: FAIL because `add_disposition` has no `finding` argument and `disposition` has no `--input` / `--finding-id` arguments.

### Task 2: Implement trusted new-finding identity

**Files:**
- Modify: `agent/triage.py:87-119`
- Modify: `agent/triage_cli.py:30-48`

- [x] **Step 1: Extend `add_disposition` without changing stored schema**

Add optional `finding: dict[str, object] | None = None`. Resolve identity from the baseline if present; otherwise require `finding` and require its computed fingerprint to equal `fingerprint`. Build the stored `tool` and `rule_id` from `_baseline_entry(finding)`, but do not append it to the baseline.

- [x] **Step 2: Add mutually exclusive CLI selection**

Make `--fingerprint` and `--finding-id` mutually exclusive. Add optional `--input Path`; reject `--finding-id` without `--input`, reject `--input` without `--finding-id`, and reject a selected ID that occurs zero or more than once. Use `_findings()` to validate the input schema before calling `add_disposition`.

- [x] **Step 3: Run focused tests after implementation**

Run: `python -m unittest tests.test_triage -v`

Expected: all triage tests pass, including existing baseline compatibility tests.

### Task 3: Align real-PR operator documentation

**Files:**
- Modify: `docs/trial-phase-2.md`
- Modify: `docs/trial-phase-2-log.md`

- [x] **Step 1: Update the real-PR disposition command**

Replace the fingerprint placeholder command with:

```powershell
.\.venv\Scripts\python.exe -m agent.triage_cli disposition `
  --store .codesec\triage.json `
  --input artifacts\findings.json `
  --finding-id <finding-id> `
  --resolution <true_positive|false_positive|accepted_risk|needs_fix> `
  --reviewer <human-reviewer> `
  --machine-label <confirmed|suspicious|possible_false_positive> `
  --note "<one-sentence, non-sensitive reason>"
```

Explain that the input is read locally, only safe identity fields are stored, and old baseline entries may still use `--fingerprint`.

- [x] **Step 2: Complete non-sensitive operational records**

Add a rule-ID summary column to the PR log. Expand false-negative seeds with PR/run or controlled reference, risk basis, non-match reason, and future detector/rule direction; state that no source/path/line/evidence may be recorded.

### Task 4: Validate the operating repair

**Files:**
- Test: `tests/test_triage.py`
- Test: full unittest suite

- [x] **Step 1: Run a local CLI smoke test using a temporary findings document**

Create only a temporary directory. Build a one-finding schema 1.0 JSON that is not in the temporary baseline; invoke `agent.triage_cli disposition --input ... --finding-id ...`; invoke `stats`; assert total is `1` and the rule is present. Delete the temporary directory automatically when the test process ends.

- [x] **Step 2: Run static and full regression checks**

Run: `git diff --check` and `python -m unittest discover -v`

Expected: no whitespace errors; 180 tests pass with only the Windows symlink test skipped when unsupported.

- [ ] **Step 3: Commit and publish for review**

```powershell
git add agent/triage.py agent/triage_cli.py tests/test_triage.py docs/trial-phase-2.md docs/trial-phase-2-log.md docs/superpowers/plans/2026-08-25-p2-new-finding-triage.md
git commit -m "feat: triage new PR findings"
git push -u origin codex/p2-triage-new-findings
```

Create a PR to `main` describing the preserved freeze boundary and the successful test results.

## Self-review

- Spec coverage: Task 1 and 2 solve the confirmed new-finding persistence gap; Task 3 completes the required non-sensitive per-PR and false-negative records; Task 4 validates the full path.
- Scope: no baseline schema, workflow, scanner, report, LLM, UI, scoring, rule-set, or merge-gate change appears in the plan.
- Compatibility: existing `--fingerprint` calls continue to resolve only known baseline entries; new-findings require a schema-validated local input plus its selected ID.
