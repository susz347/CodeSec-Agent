# Baseline and Human Triage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Store a source-free baseline and human dispositions in `.codesec/triage.json`, then classify current findings and report calibration statistics.

**Architecture:** `agent/triage.py` owns the versioned JSON contract, stable fingerprints, comparison and statistics. `agent/triage_cli.py` provides local baseline, disposition and stats commands. It consumes normalized finding documents and never reads source files.

**Tech Stack:** Python standard library, unittest, JSON.

---

### Task 1: Baseline contract and comparison

**Files:** Create `agent/triage.py`; create `tests/test_triage.py`.

- [ ] Write failing tests for stable fingerprints across line-number changes, `new` and `existing` current findings, and `resolved` baseline fingerprints.
- [ ] Run `python -m unittest -v tests.test_triage` and confirm import failures.
- [ ] Implement fingerprinting, schema 1.0 loading/saving, baseline creation and comparison without code snippets in persisted data.
- [ ] Re-run `python -m unittest -v tests.test_triage` and confirm pass.

### Task 2: Human disposition and calibration statistics

**Files:** Modify `agent/triage.py`; modify `tests/test_triage.py`.

- [ ] Write failing tests that upsert a disposition and count `false_positive`, `true_positive`, `accepted_risk` and `needs_fix` by tool/rule/machine label.
- [ ] Run the focused test and confirm failure.
- [ ] Implement validated disposition storage and grouped statistics.
- [ ] Re-run the focused test and confirm pass.

### Task 3: Local CLI and documentation

**Files:** Create `agent/triage_cli.py`; modify `docs/deployment-steps.md`; modify `docs/roadmap.md`.

- [ ] Write failing CLI tests for baseline initialization, disposition recording and stats output.
- [ ] Implement argparse subcommands with explicit file paths and no network access.
- [ ] Document local commands and keep CI/LLM scope unchanged.
- [ ] Run `python -m unittest discover -v` and `git diff --check`.
