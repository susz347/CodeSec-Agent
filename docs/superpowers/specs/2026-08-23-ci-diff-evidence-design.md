# CI Diff Evidence and Test Workflow Design

## Goal

Make the existing context-evidence and PR-diff capabilities run in the real
security workflow, and continuously verify the complete test suite in an
independent workflow.

## Scope

### Security scan workflow

For `pull_request` events, the workflow checks out the PR head and obtains the
base commit identified by `github.event.pull_request.base.sha`. It writes a
zero-context unified diff from base to head to `artifacts/pr.diff`, then passes
`--repo-root .` and `--diff artifacts/pr.diff` to `agent.cli`.

For `workflow_dispatch`, the workflow deliberately does not create or pass a
diff. The scan remains a full-repository scan and all analysis items retain the
default `diff_status` of `unknown`.

The generated diff is an internal workflow input; it is not uploaded as a
report artifact.

### Test workflow

Add `.github/workflows/test.yml`, triggered for pull requests and manual runs.
It installs Python 3.12 and Node 20, installs the pinned Python and Node
dependencies, then runs `python -m unittest discover -v`. Node installation is
required because the test suite includes DOCX rendering tests.

## Security and Failure Behavior

The workflow uses the event-provided base SHA only for same-repository PRs,
which are already guarded by the existing workflow condition. It explicitly
checks out the PR head SHA and fetches the base SHA before creating the diff.
Any checkout, fetch, diff, dependency-install, scan, or test failure fails its
job; no fallback silently substitutes a different comparison range.

## Verification

Tests will assert the documented workflow shape: PR analysis receives both the
repository root and the generated diff, while manual dispatch does not require
either a base or head SHA. The full unittest suite and `git diff --check` are
run after implementation.
