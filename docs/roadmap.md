# Roadmap

## Week 1: PR-Agent Baseline

Goal: run the original PR-Agent successfully.

Tasks:

- Prepare GitHub test repository.
- Add PR-Agent GitHub Action.
- Add model API key to GitHub Secrets.
- Open a test pull request.
- Collect screenshots and output examples.

Deliverables:

- Working PR-Agent review comment.
- Screenshot of GitHub Actions run.
- Notes on configuration and API model used.

## Week 2: Static Security Scan

Goal: add traditional security scanning.

Tasks:

- Run Semgrep on the test repository.
- Run Bandit if the repository contains Python code.
- Run npm audit if the repository contains Node.js dependencies.
- Save scanner output as JSON.
- Write a simple parser to summarize findings.

Deliverables:

- `semgrep-result.json`
- `bandit-result.json` or `npm-audit-result.json`
- Initial Markdown summary.

## Week 3: LLM Security Analysis

Goal: transform raw scanner output into useful review explanations.

Tasks:

- Design prompt for security review.
- Feed scanner results and code snippets into LLM.
- Generate vulnerability explanation and fix suggestions.
- Add OWASP/CWE references manually at first.

Deliverables:

- `security_review.md` prompt.
- Sample LLM analysis output.
- Improved Markdown report.

## Week 4: Portfolio Packaging

Goal: make the project presentable.

Tasks:

- Write README.
- Draw architecture diagram.
- Prepare demo repository.
- Generate one complete sample audit report.
- Record a 2-3 minute demo video.
- Write resume bullets and interview script.

Deliverables:

- Public GitHub repository.
- Project screenshots.
- Demo report.
- Resume description.
- Interview explanation.

## Later Upgrades

- Add RAG knowledge base for OWASP/CWE.
- Build a small web UI.
- Export Word/PDF report.
- Add GitHub issue or PR comment integration.
- Support multi-language repositories.
- Add severity scoring and false-positive filtering.

