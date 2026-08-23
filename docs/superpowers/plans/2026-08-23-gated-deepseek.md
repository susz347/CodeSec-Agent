# Gated DeepSeek Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Invoke DeepSeek only for newly introduced, high-priority findings with complete local evidence, while preserving deterministic per-finding fallback.

**Architecture:** `LlmReviewer` first builds deterministic items for every finding. It selects only `changed + new + error + confirmed + complete evidence` items, sends that bounded batch to a standard-library DeepSeek client using JSON Output, then replaces only valid returned verdicts. Every non-selected, missing, malformed, timed-out, or failed item remains deterministic.

**Tech Stack:** Python standard library (`urllib`, `json`), unittest, GitHub Actions secret environment variable.

---

### Task 1: Gate selection and fallback behavior

**Files:** Modify `agent/security_reviewer.py`; modify `tests/test_llm.py`.

- [x] Write failing tests proving only a changed, new, error-severity, deterministic-confirmed finding with an untruncated evidence window is sent; all other findings keep deterministic analysis.
- [x] Run `python -m unittest tests.test_llm -v` and confirm the new gate test fails.
- [x] Add a private gate predicate and make `LlmReviewer` analyze deterministically first, request only candidates, and retain deterministic items for non-candidates, omitted IDs, and contract failures.
- [x] Re-run `python -m unittest tests.test_llm -v` and confirm pass.

### Task 2: DeepSeek transport

**Files:** Modify `agent/llm.py`; modify `tests/test_llm.py`.

- [x] Write failing tests for the POST request shape, `Authorization` header, JSON Output setting, response extraction, and transport failure without exposing API keys.
- [x] Run `python -m unittest tests.test_llm -v` and confirm the transport tests fail.
- [x] Add `DeepSeekClient` using `urllib.request`, fixed HTTPS endpoint/model/token/timeout defaults, `response_format={"type":"json_object"}`, prompt text that requires JSON, and typed transport errors.
- [x] Re-run `python -m unittest tests.test_llm -v` and confirm pass.

### Task 3: Explicit CLI and CI enablement

**Files:** Modify `agent/cli.py`, `.github/workflows/security-scan.yml`, `tests/test_agent_cli.py`, `tests/test_workflows.py`, `docs/deployment-steps.md`.

- [x] Write failing tests for `--backend deepseek` using an injected fake client factory and for the workflow only enabling that backend when `DEEPSEEK_API_KEY` is present.
- [x] Run focused tests and confirm failure.
- [x] Add `--backend deterministic|deepseek`, construct the client only from the process environment, and make the workflow pass that backend only when the existing secret is non-empty.
- [x] Document the data-egress boundary, gate, environment secret, timeout/token cap, and deterministic fallback.
- [x] Run the full unittest suite and `git diff --check`.
