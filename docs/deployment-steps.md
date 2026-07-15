# Deployment Steps

## Phase 1: Run PR-Agent With GitHub Actions

### Prerequisites

- GitHub account.
- A test repository.
- One LLM API key, such as OpenAI, Claude, Gemini, DeepSeek, or another provider supported by PR-Agent.
- Basic GitHub Actions knowledge.

### Add Workflow

Create `.github/workflows/pr-agent.yml` in the test repository:

```yaml
name: PR Agent

on:
  pull_request:
    types: [opened, reopened, ready_for_review, synchronize]
  issue_comment:

jobs:
  pr_agent_job:
    if: ${{ github.event.sender.type != 'Bot' }}
    runs-on: ubuntu-latest
    permissions:
      issues: write
      pull-requests: write
      contents: write
      checks: write
    steps:
      - name: PR Agent action step
        uses: the-pr-agent/pr-agent@main
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Add Secret

In GitHub:

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

Add:

```text
OPENAI_KEY = your_api_key
```

`GITHUB_TOKEN` is automatically provided by GitHub Actions.

### Verify

1. Create a new branch.
2. Make a small code change.
3. Open a pull request.
4. Confirm PR-Agent comments on the PR.
5. Save screenshots of the review result.

## Phase 2: Run PR-Agent Locally

Install:

```bash
pip install pr-agent
```

Set API key on Windows PowerShell:

```powershell
$env:OPENAI_KEY="your_api_key"
```

Run:

```bash
pr-agent --pr_url https://github.com/owner/repo/pull/123 review
```

## Phase 3: Add Static Security Scanners

### Semgrep

Install or run with Docker.

Basic command:

```bash
semgrep scan --config auto --json -o semgrep-result.json .
```

Docker on Windows:

```bash
docker run --rm -v "%cd%:/src" semgrep/semgrep semgrep scan --config auto --json -o /src/semgrep-result.json /src
```

### Bandit

For Python projects:

```bash
pip install bandit
bandit -r . -f json -o bandit-result.json
```

### npm audit

For Node.js projects:

```bash
npm audit --json > npm-audit-result.json
```

## Phase 4: Generate Security Report

Minimum report fields:

- Project name.
- Scan time.
- Scanner results.
- Vulnerability location.
- Risk level.
- Cause.
- Impact.
- Fix suggestion.
- Reference knowledge, such as CWE or OWASP.

First output format should be Markdown. Word/PDF export can be added later.

