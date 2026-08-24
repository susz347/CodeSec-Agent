# CodeSec-Agent

CodeSec-Agent 是一个基于 [PR-Agent](https://github.com/The-PR-Agent/pr-agent) 的代码安全审计与修复建议系统。项目将 Pull Request 代码审查、静态应用安全测试、漏洞知识库和大模型推理能力结合起来，生成结构化的安全审计报告。

项目重点不是通用代码点评，而是面向安全场景的代码审查流程：先由静态扫描工具提供可复现的技术证据，再由 Agent 层完成风险解释、影响分析、修复建议和报告生成。

## 项目概述

现代代码审查流程通常擅长发现代码风格、可维护性和逻辑回归问题，但安全审查还需要更稳定的漏洞模式识别能力。Semgrep、Bandit 等静态扫描工具可以发现已知风险模式，而大模型 Agent 更适合解释上下文、归纳影响并生成开发者可理解的修复建议。

CodeSec-Agent 的目标是连接这两类能力：

```text
Pull Request / 代码仓库
  -> PR-Agent 获取代码变更上下文
  -> Semgrep / Bandit / npm audit 输出安全扫描结果
  -> 安全分析 Agent 解释风险
  -> 生成风险等级、影响分析和修复建议
  -> 输出 Markdown 安全审计报告
```

## 为什么需要结合 PR 审查和安全扫描？

PR-Agent 和静态安全扫描工具解决的是不同层次的问题。

| 能力 | PR-Agent / LLM 审查 | 静态安全扫描工具 |
| --- | --- | --- |
| 主要作用 | 理解代码变更并生成审查解释 | 基于规则发现已知漏洞模式 |
| 优势 | 能结合上下文给出自然语言建议 | 稳定、可复现、适合批量扫描 |
| 局限 | 可能漏掉特定漏洞模式，输出不完全稳定 | 可能缺少业务上下文，存在误报 |
| 在本项目中的角色 | 负责解释、归纳、排序和修复建议 | 负责发现问题并提供技术证据 |

在 CodeSec-Agent 中，扫描工具负责提供文件路径、行号、规则 ID、风险等级等证据；Agent 层负责把这些证据转化为开发者能理解和执行的安全审计结论。

## 系统架构

```text
CodeSec-Agent
├─ PR 审查层
│  └─ 基于 PR-Agent 获取 Pull Request diff 和代码审查上下文
├─ 静态扫描层
│  └─ 运行 Semgrep、Bandit、npm audit 收集安全发现
├─ 安全分析层
│  └─ 结合扫描结果、代码片段和安全知识生成漏洞解释
└─ 报告生成层
   └─ 输出 Markdown 报告，后续扩展 Word/PDF
```

## 核心能力

- 基于 PR-Agent 的 Pull Request 审查工作流。
- 接入 Semgrep、Bandit 等静态安全扫描工具。
- 支持 npm audit 依赖漏洞结果接入。
- 解析并归一化不同扫描器的 JSON 输出。
- 使用安全审查 Prompt 生成漏洞解释和修复建议。
- 输出包含风险等级、位置、原因、影响和修复方案的 Markdown 报告。
- 后续扩展 OWASP/CWE 知识库增强解释依据。

## 审计报告内容

生成的安全审计报告计划包含：

- 仓库或 Pull Request 基本信息。
- 扫描结果摘要。
- 漏洞文件和代码位置。
- 风险等级。
- 扫描规则 ID 或漏洞类别。
- 问题成因分析。
- 潜在影响说明。
- 修复建议。
- CWE、OWASP 或安全编码规范参考。

## 仓库结构

```text
CodeSec-Agent/
  .github/
    workflows/
      pr-agent.yml
      security-scan.yml
  .gitignore
  .pr_agent.toml
  README.md
  agent/
    cli.py
    context.py
    diff.py
    knowledge.py
    llm.py
    models.py
    security_reviewer.py
    prompts/security_review.md
  docs/
    beginner-guide.md
    deployment-steps.md
    prerequisites.md
    project-checklist.md
    roadmap.md
    superpowers/specs/  superpowers/plans/
  examples/
    security-report.md
  prompts/
    security_review.md
  reporting/
    cli.py
    load_findings.py
    manifest.py
    models.py
    risk.py
    render_analysis.py
    render_json.py  render_markdown.py  render_excel.py
    render_docx.py  render_docx.js  render_pdf.py
    summary.py
  scanner/
    models.py
    normalize_semgrep.py  normalize_bandit.py  normalize_npm_audit.py
    run_semgrep.py  run_bandit.py  run_npm_audit.py
  tests/
  push-to-github.ps1
```

## 快速开始

项目按统一阶段实施：

1. **Phase 1：GitHub Actions PR-Agent**。
2. **Phase 2：本地 PR-Agent CLI**。
3. **Phase 3：静态安全扫描与结果归一化**。
4. **Phase 4：Agent 分析、报告与自动化**。

Phase 1/2 的仓库配置和本地 CLI 安装已实施并通过静态验证，但真实 GitHub Action 与本地 CLI 的端到端验证仍待完成。DeepSeek 接入、最小权限、验证和故障排查统一维护在 [部署与运行步骤](docs/deployment-steps.md) 中；README 不保存容易过期的 workflow、TOML 或命令副本。

## 开发路线

产品研发阶段、任务和交付物统一维护在 [项目路线图](docs/roadmap.md) 中；其中 Phase 1/2 与部署指南一致，分别对应 GitHub Action 和本地 CLI。

## 设计原则

- **证据优先**：以扫描器发现作为安全分析的基础输入。
- **面向开发者**：报告输出应便于开发者理解和修复，而不是只给安全人员阅读。
- **模块可替换**：扫描、分析和报告生成模块应保持低耦合。
- **审慎结论**：系统用于辅助安全审查，不声称替代专业安全审计。

## 当前状态

Phase 1/2（PR-Agent 双入口）与 Phase 3（Semgrep/Bandit/npm audit 归一化）已完成。Phase 4 已完成本地多格式报告（JSON/Markdown/Excel/DOCX/PDF）、确定性分析 Agent（确认/可疑/误报分类、CWE/OWASP 知识库、修复建议）、完整示例报告与安全扫描 GitHub Action（默认只提示不阻断）。分析层已扩展上下文证据（安全路径约束 + 行/字节预算）与 PR diff 过滤（changed/unchanged/unknown），并落地全格式 analysis、确定性风险排序与带 SHA-256 的产物清单。真实 DeepSeek 调用、分支推送与合并阻断策略留待单独授权：

```text
PR-Agent 审查
  + Semgrep/Bandit/npm audit 归一化
  + 确定性安全分析 Agent
  + 上下文证据 + PR diff 过滤
  + 全格式 analysis + 风险排序 + 产物清单
  + 多格式报告 + 完整示例报告
  + 安全扫描 CI（仅提示，不阻断）
```

## 文档

- [新手学习指南](docs/beginner-guide.md)
- [前置知识](docs/prerequisites.md)
- [部署步骤](docs/deployment-steps.md)
- [故障 Runbook](docs/runbook.md)
- [发布验收清单](docs/acceptance-checklist.md)
- [产物保留与归档策略](docs/retention-policy.md)
- [项目路线图](docs/roadmap.md)
- [项目任务清单](docs/project-checklist.md)
