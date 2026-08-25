# Trial Phase 2 Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a measurable, non-blocking 2–4 week security-scan trial with auditable human triage and a decision-ready P2 review.

**Architecture:** Keep the existing scanner, deterministic analysis, gated DeepSeek path, workflow behaviour, and triage schema unchanged. Add one canonical operating specification and one non-sensitive trial log; link them from the existing Runbook and roadmap. `.codesec/triage.json` remains the versioned baseline and human-disposition store, while timing, PR-level metrics, and de-identified missed coverage live only in the trial log.

**Tech Stack:** Markdown, existing `.codesec/triage.json`, `agent.triage_cli`, GitHub Actions, Python unittest.

---

## File structure

| File | Responsibility |
| --- | --- |
| `.gitignore` | Ignore local linked-worktree metadata. |
| `docs/trial-phase-2.md` | Canonical trial scope, cadence, metrics, exit criteria, and frozen-capability restart triggers. |
| `docs/trial-phase-2-log.md` | Copyable, non-sensitive PR, metric, calibration, and missed-coverage record. |
| `docs/runbook.md` | Point operators to the canonical Phase 2 operating rules. |
| `docs/roadmap.md` | Record the completed P0 entry and current Phase 2 operational state. |

### Task 1: Protect local worktree metadata

**Files:**
- Modify: `.gitignore`
- Test: `git check-ignore -v .worktrees/example/HEAD`

- [x] **Step 1: Add the local worktree rule**

Add this line after `node_modules/`:

```gitignore
.worktrees/
```

- [x] **Step 2: Verify the rule**

Run: `git check-ignore -v .worktrees/example/HEAD`

Expected: output identifies `.gitignore` and `.worktrees/`.

- [x] **Step 3: Commit the standalone housekeeping change**

```powershell
git add .gitignore
git commit -m "chore: ignore local worktrees"
```

### Task 2: Write the canonical Phase 2 operating specification

**Files:**
- Create: `docs/trial-phase-2.md`
- Test: manual Markdown-link and requirement review

- [x] **Step 1: Define scope and non-negotiable boundaries**

Document that RAG, numeric risk scoring, Web UI, scanner-rule expansion, and merge-gate activation are frozen; scans remain non-blocking and work continues only on `codex/*` PR branches.

- [x] **Step 2: Define the operating cadence and triage record**

Document real same-repository PR handling, required human disposition fields, the existing `agent.triage_cli disposition` command, and the prohibition on using `baseline` to rewrite a live disposition store without a separately reviewed backup.

- [x] **Step 3: Define measurable P2 review criteria**

Document the 15-real-PR, 30-human-disposition, and three-dispositions-per-rule criteria; separate accuracy from operational-burden metrics; require a `保留 / 调整 / 排除` decision for every tuning point. Define balanced confirmed-risk coverage and de-identified missed-coverage recording without manufacturing samples.

- [x] **Step 4: Define restart triggers**

Document evidence thresholds for reconsidering merge gates, RAG, scoring, UI, and scanner-rule expansion. State that satisfying a trigger permits a proposal only, not implementation in this phase.

- [x] **Step 5: Verify the specification against the approved instruction**

Confirm each listed frozen item, metric, calibration requirement, and restart condition appears once and does not change a workflow, scanner rule, or product schema.

### Task 3: Add the non-sensitive trial log template

**Files:**
- Create: `docs/trial-phase-2-log.md`
- Test: manual data-sensitivity review

- [x] **Step 1: Add PR and weekly-metric tables**

Include fields for PR/run references, finding and manual-review counts, analysis backend, timestamps, and aggregate elapsed time; exclude source paths, evidence snippets, report contents, and secrets.

- [x] **Step 2: Add calibration and missed-coverage tables**

Require tool/rule, machine label, terminal human resolution, one-line reason, and decision eligibility for calibration. Record missed coverage only as a de-identified future-P4 seed, not as a new rule request to implement now.

- [x] **Step 3: Add the non-counting baseline snapshot**

Record the existing 17-finding baseline and its one historical disposition as context, explicitly excluding it from real-PR and P2-exit counts.

- [x] **Step 4: Review for non-sensitive evidence**

Confirm the template contains no code, file paths, raw scanner output, API keys, personal credentials, or copied report evidence.

### Task 4: Connect operators to the new documents

**Files:**
- Modify: `docs/runbook.md`
- Modify: `docs/roadmap.md`
- Test: Markdown links resolve to tracked files

- [x] **Step 1: Link the Runbook to Phase 2 operations**

Add a short entry near the Runbook introduction that identifies `docs/trial-phase-2.md` as the trial operating authority and `docs/trial-phase-2-log.md` as the non-sensitive log.

- [x] **Step 2: Record Phase 2 status in the roadmap**

Add a `试运行期 · 第二阶段` section before future enhancements: P0 is complete; real-PR triage is in progress; links lead to the canonical specification and log.

- [x] **Step 3: Verify links**

Run: `git ls-files docs/trial-phase-2.md docs/trial-phase-2-log.md`

Expected: both paths are printed; inspect each relative Markdown link once.

### Task 5: Validate and publish the documentation-only change

**Files:**
- Test: all files above

- [x] **Step 1: Validate whitespace and repository state**

Run: `git diff --check` and `git status --short`

Expected: no whitespace errors; only the five planned tracked files are modified or added.

- [x] **Step 2: Run the full regression suite**

Run: `python -m unittest discover -v`

Expected: 180 tests pass; the platform-specific symlink test may be skipped on Windows.

- [ ] **Step 3: Commit, push, and open a PR**

```powershell
git add .gitignore docs/trial-phase-2.md docs/trial-phase-2-log.md docs/runbook.md docs/roadmap.md docs/superpowers/plans/2026-08-25-trial-phase-2-operations.md
git commit -m "docs: define trial phase 2 operations"
git push -u origin codex/trial-phase-2-operations
gh pr create --base main --head codex/trial-phase-2-operations --title "docs: define trial phase 2 operations" --body "..."
```

## Self-review

- Scope coverage: Tasks 2 and 3 cover every requirement in the approved Phase 2 instruction; Task 4 makes them discoverable; Task 1 records the approved worktree hygiene rule.
- Placeholder scan: this plan contains no implementation placeholder; the PR body ellipsis is intentionally not executable content and must be replaced with the final concrete summary before use.
- Interface consistency: No code or schema changes are planned. The existing `disposition`, `baseline`, and `stats` CLI commands remain their current interfaces.
