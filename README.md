# CodeSec-Agent

CodeSec-Agent 是一个基于 [PR-Agent](https://github.com/qodo-ai/pr-agent) 的代码安全审计与修复建议系统。项目将 Pull Request 代码审查、静态应用安全测试、漏洞知识库和大模型推理能力结合起来，生成结构化的安全审计报告。

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
  README.md
  docs/
    beginner-guide.md
    deployment-steps.md
    project-checklist.md
    roadmap.md
  prompts/
    security_review.md
  push-to-github.ps1
```

计划中的实现模块：

```text
scanner/
  run_semgrep.py
  run_bandit.py
  parse_results.py

agent/
  security_reviewer.py
  prompts/
    security_review.md
    fix_suggestion.md

knowledge/
  owasp_top10.md
  cwe_top25.md
  secure_coding.md

report/
  generate_markdown.py
  generate_docx.py
```

## 快速开始

### 1. 使用 GitHub Actions 运行 PR-Agent

在目标仓库中创建 `.github/workflows/pr-agent.yml`：

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
        uses: qodo-ai/pr-agent@main
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

在 GitHub 仓库中添加模型 API Key：

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

需要添加：

```text
OPENAI_KEY = your_api_key
```

### 2. 运行静态安全扫描

Semgrep：

```bash
semgrep scan --config auto --json -o semgrep-result.json .
```

Bandit，适用于 Python 项目：

```bash
bandit -r . -f json -o bandit-result.json
```

npm audit，适用于 Node.js 项目：

```bash
npm audit --json > npm-audit-result.json
```

### 3. 生成安全审计报告

第一阶段目标是将扫描器 JSON 输出转换为 Markdown 报告：

```text
semgrep-result.json / bandit-result.json
  -> 结果解析
  -> 发现项归一化
  -> 安全分析 Prompt
  -> Markdown 审计报告
```

## 开发路线

### Phase 1: PR 审查基线

- 配置 PR-Agent GitHub Action。
- 验证 Pull Request 自动审查评论。
- 记录最小可运行配置。

### Phase 2: 静态扫描接入

- 本地运行 Semgrep 和 Bandit。
- 将扫描结果导出为 JSON。
- 将不同扫描器结果归一化为统一结构。

### Phase 3: 安全分析 Agent

- 设计安全审查 Prompt。
- 结合扫描发现和代码片段进行分析。
- 生成漏洞解释、影响分析和修复建议。

### Phase 4: 报告生成

- 生成 Markdown 安全审计报告。
- 增加风险汇总和发现项表格。
- 增加 CWE/OWASP 参考依据。
- 扩展 Word/PDF 报告导出。

## 设计原则

- **证据优先**：以扫描器发现作为安全分析的基础输入。
- **面向开发者**：报告输出应便于开发者理解和修复，而不是只给安全人员阅读。
- **模块可替换**：扫描、分析和报告生成模块应保持低耦合。
- **审慎结论**：系统用于辅助安全审查，不声称替代专业安全审计。

## 当前状态

当前仓库处于文档设计和工作流初始化阶段。下一阶段目标是完成最小可运行闭环：

```text
PR-Agent 审查
  + Semgrep/Bandit JSON 扫描
  + Markdown 安全审计报告
```

## 文档

- [新手学习指南](docs/beginner-guide.md)
- [部署步骤](docs/deployment-steps.md)
- [项目路线图](docs/roadmap.md)
- [项目任务清单](docs/project-checklist.md)
