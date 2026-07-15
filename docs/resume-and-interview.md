# Resume and Interview Material

## Resume Project Name

CodeSec-Agent: AI Agent Based Code Security Review and Fix Suggestion System

## Resume Description

Built an AI-assisted code security review system based on PR-Agent. The system combines pull request diff analysis, static security scanning, and LLM-based reasoning to identify potential vulnerabilities, explain risk causes, and generate fix suggestions. Integrated Semgrep/Bandit scanner outputs and produced Markdown security audit reports covering vulnerability location, risk level, impact, and remediation advice.

## Chinese Resume Version

CodeSec-Agent：基于大模型 Agent 的代码安全审计与修复建议系统

- 基于 PR-Agent 构建 GitHub PR 自动审查流程，实现代码变更理解、审查意见生成和修复建议输出。
- 接入 Semgrep/Bandit 等静态分析工具，提取潜在漏洞、危险函数调用和不安全编码模式。
- 设计安全审计 Prompt，将扫描结果、代码片段和安全规范结合，生成漏洞成因解释、影响分析和修复建议。
- 支持生成 Markdown 审计报告，包含风险等级、代码位置、问题说明、修复方案和参考依据。

## 1-Minute Interview Explanation

这个项目是我基于 PR-Agent 做的代码安全审计 Agent。原始 PR-Agent 主要做通用代码 Review，我在它的基础上加入了安全扫描链路，用 Semgrep、Bandit 等工具先做静态分析，再把扫描结果和 PR diff 一起交给大模型，让它生成更适合人阅读的漏洞解释和修复建议。最后系统会输出一份 Markdown 安全审计报告，包括漏洞位置、风险等级、影响范围和修复建议。这个项目的重点不是单纯调用大模型，而是把传统静态分析工具和 Agent 工作流结合起来，提升代码安全审查的效率和可解释性。

## Advisor Interview Angle

This project can be introduced as a software engineering and cybersecurity intersection:

- AI Agent for software engineering.
- Code security review.
- Trustworthy software.
- Static analysis plus LLM reasoning.
- Vulnerability explanation and repair suggestion.

## Job Interview Angle

Emphasize engineering implementation:

- GitHub Actions integration.
- CLI/local execution.
- Scanner integration.
- JSON parsing.
- Prompt design.
- Report generation.
- Deployment and demo.

## Avoid Overclaiming

Do not claim:

- The system can replace professional security auditing.
- The system guarantees all vulnerabilities are found.
- The system performs penetration testing or exploit generation.

Better wording:

- It assists code security review.
- It improves review efficiency.
- It combines static analysis and LLM explanation.
- It provides human-readable remediation suggestions.

