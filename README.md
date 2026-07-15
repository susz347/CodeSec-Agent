# CodeSec-Agent

CodeSec-Agent is a planned portfolio project based on PR-Agent. The goal is to build an AI-assisted code security review system that can analyze pull requests or repositories, combine static analysis results with LLM reasoning, and generate security-focused review reports.

## Project Positioning

This project is designed for three use cases:

1. Engineering master's advisor matching: show interest in AI Agent, cybersecurity, trustworthy software, and key software engineering.
2. Resume project: demonstrate practical ability in Agent workflow, static analysis, security review, RAG, and report generation.
3. Job interviews: provide a concrete engineering demo beyond a generic chatbot or PDF Q&A system.

## Core Idea

Base system:

- PR-Agent for pull request review, code explanation, and improvement suggestions.
- Semgrep, Bandit, and npm audit for static analysis.
- OWASP/CWE/security coding materials as a lightweight knowledge base.
- Markdown or Word report generation for final audit output.

Final system goal:

```text
Pull Request / Repository
  -> PR-Agent diff understanding
  -> Static security scan
  -> LLM security analysis
  -> Vulnerability explanation and fix suggestions
  -> Audit report
```

## Recommended First Demo

The first working demo should be intentionally small:

1. Create a GitHub test repository.
2. Deploy PR-Agent with GitHub Actions.
3. Open a pull request and confirm automated review works.
4. Run Semgrep/Bandit locally against the same repository.
5. Convert scan JSON into a Markdown security audit report.

## Why This Project Fits

- It is close to AI Agent, not just ordinary RAG.
- It connects naturally with cybersecurity and software engineering.
- It can be explained clearly in advisor interviews and job interviews.
- It leaves room for progressive upgrades: GitHub Action, CLI, static scanners, RAG, web UI, report export.

