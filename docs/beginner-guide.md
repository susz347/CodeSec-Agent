# 新手学习指南

本文面向第一次接触 AI Agent、PR 自动审查和代码安全扫描的读者。阅读目标不是立即掌握所有实现细节，而是先理解 CodeSec-Agent 的工作流、模块边界和最小可运行闭环。

## 项目要解决的问题

代码审查通常关注可读性、可维护性和逻辑正确性。安全审查还需要识别危险函数、输入校验缺失、依赖漏洞、敏感信息泄露等风险。

CodeSec-Agent 的长期目标是把代码审查、静态扫描和大模型分析串成一条流程：

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

本项目在后续路线图阶段计划接入：

- Semgrep：通用静态分析和安全规则扫描工具。
- Bandit：Python 代码安全扫描工具。
- npm audit：Node.js 依赖漏洞扫描工具。

### Agent 安全分析

扫描器输出通常是 JSON，适合机器处理，但不适合直接交给开发者阅读。

Agent 安全分析层负责把扫描结果转成可读结论，包括问题原因、影响范围、修复建议和参考依据。

### 审计报告

审计报告是后续阶段的最终输出，计划先使用 Markdown，再扩展 Word 或 PDF；它不属于当前 Phase 1/2 最小闭环。

一份最小可用报告应包含漏洞位置、风险等级、证据、影响说明、修复建议和参考链接。

## 建议阅读顺序

1. 阅读 [README](../README.md)，了解项目目标和总体架构。
2. 阅读 [前置知识](prerequisites.md)，补齐必要基础。
3. 按 [部署与运行步骤](deployment-steps.md) 跑通 Phase 1 GitHub Action 和 Phase 2 本地 CLI。
4. 阅读 [安全审查 Prompt](../prompts/security_review.md)，理解当前审查输出约束。
5. 阅读 [项目路线图](roadmap.md) 和 [任务清单](project-checklist.md)，了解静态扫描、结果解析与报告的后续顺序。

## 最小可运行闭环

当前最小闭环只包含两个 PR-Agent 运行入口：

```text
Phase 1：GitHub Actions PR-Agent
-> 同仓库验证 PR
-> GitHub Actions 自动运行 PR-Agent review
-> 在 PR 中产生 Action 审查评论

Phase 2：本地 PR-Agent CLI
-> 同一个验证 PR
-> Windows 本地 PR-Agent CLI 使用 main 中的可信配置
-> 在 PR 中产生本地触发的审查评论
-> 清理临时凭据、验证 PR、分支和探针
```

Semgrep、Bandit、npm audit 和结果解析属于 [Phase 3：静态安全扫描与结果归一化](roadmap.md)，Agent 综合分析、Markdown 报告与自动化属于 [Phase 4：Agent 分析、报告与自动化](roadmap.md)；它们不是当前 Phase 1/2 的完成条件。

## 常见误区

### 误区一：当前没接扫描器，就永远不需要扫描器

AI Review 擅长解释上下文，但输出不一定稳定。扫描器基于规则运行，可以提供可复现的技术证据。

本项目的长期方案仍会结合二者：当前先验证 PR-Agent 的两个运行入口；后续由扫描器提供可复现发现，再由 Agent 解释问题。

### 误区二：第一版就要做 RAG

第一版可以先使用人工整理的 OWASP/CWE 摘要作为参考材料。只有当报告解释需要更丰富的知识来源时，再引入 RAG。

### 误区三：必须修改 PR-Agent 源码

当前 Phase 1/2 不需要修改 PR-Agent 源码。先依次跑通 GitHub Action 和本地 CLI，再按路线图扩展扫描与报告模块。

## 下一步

完成阅读后，建议按下面顺序动手：

1. 按权威部署指南完成 Phase 1 GitHub Action。
2. 对同一个短生命周期验证 PR 完成 Phase 2 本地 CLI。
3. 关闭且不合并验证 PR，安全清理分支、探针和临时凭据。
4. Phase 1/2 验收后，再按路线图进入静态扫描、结果归一化和报告阶段。
