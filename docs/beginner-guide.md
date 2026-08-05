# 新手学习指南

本文面向第一次接触 AI Agent、PR 自动审查和代码安全扫描的读者。阅读目标不是立即掌握所有实现细节，而是先理解 CodeSec-Agent 的工作流、模块边界和最小可运行闭环。

## 项目要解决的问题

代码审查通常关注可读性、可维护性和逻辑正确性。安全审查还需要识别危险函数、输入校验缺失、依赖漏洞、敏感信息泄露等风险。

CodeSec-Agent 的目标是把代码审查、静态扫描和大模型分析串成一条流程：

```text
读取 PR 或仓库代码
-> 运行安全扫描
-> 收集结构化发现
-> 结合代码上下文进行安全分析
-> 输出可读的审计报告
```

## 先理解五个核心概念

### Pull Request

Pull Request，简称 PR，是一次待合并的代码变更。审查系统通常会读取 PR diff，也就是本次新增、删除或修改的代码。

### PR-Agent

PR-Agent 是开源 AI code review agent。它可以接入 GitHub Pull Request，自动生成 review、改进建议和问答回复。

在本项目中，PR-Agent 负责提供 PR 审查入口和代码变更上下文。

### 静态安全扫描

静态扫描是不运行程序、直接分析源代码或依赖清单的安全检查方式。它适合发现已知风险模式。

本项目计划接入：

- Semgrep：通用静态分析和安全规则扫描工具。
- Bandit：Python 代码安全扫描工具。
- npm audit：Node.js 依赖漏洞扫描工具。

### Agent 安全分析

扫描器输出通常是 JSON，适合机器处理，但不适合直接交给开发者阅读。

Agent 安全分析层负责把扫描结果转成可读结论，包括问题原因、影响范围、修复建议和参考依据。

### 审计报告

审计报告是最终输出。第一阶段使用 Markdown，后续可扩展 Word 或 PDF。

一份最小可用报告应包含漏洞位置、风险等级、证据、影响说明、修复建议和参考链接。

## 建议阅读顺序

1. 阅读 `README.md`，了解项目目标和总体架构。
2. 阅读 `docs/prerequisites.md`，补齐必要前置知识。
3. 阅读 `docs/deployment-steps.md`，理解如何跑通 PR-Agent 和扫描器。
4. 阅读 `prompts/security_review.md`，理解 Agent 输出报告的格式要求。
5. 阅读 `docs/roadmap.md` 和 `docs/project-checklist.md`，了解后续开发顺序。

## 最小可运行闭环

第一阶段不追求复杂功能，先完成下面的闭环：

```text
测试 PR
-> PR-Agent 自动审查
-> Semgrep/Bandit 输出 JSON
-> 解析扫描结果
-> 生成 Markdown 安全报告
```

这个闭环跑通后，再考虑知识库增强、报告格式扩展、Web 界面和 PR 评论集成。

## 常见误区

### 误区一：有 AI Review 就不需要扫描器

AI Review 擅长解释上下文，但输出不一定稳定。扫描器基于规则运行，可以提供可复现的技术证据。

本项目采用二者结合的方式：扫描器负责发现问题，Agent 负责解释问题。

### 误区二：第一版就要做 RAG

第一版可以先使用人工整理的 OWASP/CWE 摘要作为参考材料。只有当报告解释需要更丰富的知识来源时，再引入 RAG。

### 误区三：必须修改 PR-Agent 源码

第一阶段不需要修改 PR-Agent 源码。先通过 GitHub Action 或 CLI 跑通 PR-Agent，再围绕扫描和报告模块进行扩展。

## 下一步

完成阅读后，建议按下面顺序动手：

1. 配置 GitHub Action 跑通 PR-Agent。
2. 在本地运行 Semgrep 或 Bandit。
3. 保存扫描结果 JSON。
4. 设计统一的 finding 数据结构。
5. 生成第一份 Markdown 审计报告。
