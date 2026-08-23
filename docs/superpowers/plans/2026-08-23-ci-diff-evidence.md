# CI Diff Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run context evidence and PR diff classification in the security workflow, and verify all tests in a dedicated CI workflow.

**Architecture:** The security workflow owns Git state: only a PR run checks out the head SHA, fetches its base SHA, and creates an internal zero-context diff. The Python CLI only consumes a repository root and diff file. A separate test workflow installs the same dependencies and runs the full unittest suite.

**Tech Stack:** GitHub Actions, Git, Python unittest, Node.js/npm.

---

### Task 1: Lock workflow behavior with static tests

**Files:** Create `tests/test_workflows.py`; modify `.github/workflows/security-scan.yml`; create `.github/workflows/test.yml`.

- [ ] Write failing tests that read workflow YAML as text and assert the security workflow contains `github.event.pull_request.base.sha`, `--repo-root .`, and `--diff artifacts/pr.diff`, while the test workflow contains `npm install --ignore-scripts` and `python -m unittest discover -v`.
- [ ] Run `python -m unittest -v tests.test_workflows`; it must fail because the files/arguments do not yet exist.

### Task 2: Connect PR diff and context evidence

**Files:** Modify `.github/workflows/security-scan.yml`; test `tests/test_workflows.py`.

- [ ] For PR runs, explicitly check out `${{ github.event.pull_request.head.sha }}`, fetch `${{ github.event.pull_request.base.sha }}`, and create `artifacts/pr.diff` with `git diff --no-ext-diff --unified=0 "$BASE_SHA" "$HEAD_SHA"`.
- [ ] Pass `--repo-root .` for every analysis run. Pass `--diff artifacts/pr.diff` only in the PR analysis step; manual dispatch has no diff step and therefore preserves `unknown` status.
- [ ] Run `python -m unittest -v tests.test_workflows`; it must pass.

### Task 3: Add independent test CI

**Files:** Create `.github/workflows/test.yml`; test `tests/test_workflows.py`.

- [ ] Add `pull_request` and `workflow_dispatch` triggers, read-only contents permission, Python 3.12 and Node 20 setup, pinned Python/Node dependency installation, and `python -m unittest discover -v`.
- [ ] Run `python -m unittest -v tests.test_workflows`; it must pass.

### Task 4: Document and verify

**Files:** Modify `docs/deployment-steps.md`; create/modify the files above.

- [ ] Document that PR scans receive context evidence and changed/unchanged/unknown classification, while manually dispatched full scans intentionally retain unknown diff status.
- [ ] Run `python -m unittest discover -v` and `git diff --check`.
- [ ] Commit the design, plan, workflow, test, and documentation together using message `ci: test security workflow diff evidence`.
