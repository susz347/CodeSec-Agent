# CodeSec-Agent 新手学习指南

这份文档是给“刚开始了解 Agent 和代码安全审计”的同学看的。你不需要一开始就懂 PR-Agent、Semgrep、Bandit 或 RAG，先把项目的整体逻辑弄清楚就可以。

## 你先把这个项目理解成什么？

把 CodeSec-Agent 想成一个“代码安全审计助手”。

它做的事情不是简单聊天，而是围绕代码完成一条工作流：

```text
拿到代码变更
-> 看懂这次改了什么
-> 扫描有没有常见安全风险
-> 解释风险为什么存在
-> 给出修复建议
-> 输出一份审计报告
```

如果面试官问你这个项目是什么，你可以先这样说：

> 这是一个基于 PR-Agent 的代码安全审计项目。我用 PR-Agent 做 Pull Request 代码审查，再接入 Semgrep、Bandit 这类静态分析工具发现安全问题，最后用大模型把扫描结果解释成可读的漏洞说明和修复建议，并生成 Markdown 审计报告。

## 先理解 5 个核心概念

### 1. Pull Request

Pull Request 简称 PR，可以理解成“我改了一些代码，请你帮我检查后再合并”。

代码审查工具通常会看 PR 里的 diff，也就是这次新增、删除、修改了哪些代码。

### 2. PR-Agent

PR-Agent 是一个开源 AI code review agent。它可以在 GitHub PR 里自动评论，帮助总结代码变更、发现潜在问题、提出改进建议。

在本项目里，PR-Agent 是底座。我们不是从零写一个代码审查机器人，而是基于它扩展安全审计能力。

### 3. 静态安全扫描

静态扫描就是“不运行程序，直接看代码”，通过规则发现潜在问题。

常见工具：

- Semgrep：通用代码规则扫描工具，支持多种语言。
- Bandit：Python 安全扫描工具。
- npm audit：Node.js 依赖漏洞扫描工具。

### 4. Agent 分析

扫描工具会输出 JSON，但 JSON 不适合直接给人看。

Agent 分析层要做的是把扫描结果翻译成人能理解的内容：

- 这个问题在哪里？
- 为什么危险？
- 可能造成什么影响？
- 应该怎么修？
- 可以参考哪个 CWE/OWASP 条目？

### 5. 审计报告

审计报告是最终展示成果。第一版用 Markdown 就够了。

一份最小可用报告应该包含：

- 项目名称
- 扫描时间
- 风险总览
- 漏洞位置
- 风险等级
- 问题原因
- 影响说明
- 修复建议
- 参考依据

## 为什么 PR-Agent 审查不够，还要安全扫描？

因为 AI 审查和安全扫描擅长的事情不同。

PR-Agent 更像“会读代码的审查同学”，它能理解上下文、总结改动、给出自然语言建议。但它不一定稳定，每次输出可能不完全一样，也可能漏掉隐藏的安全问题。

Semgrep、Bandit 这类工具更像“规则检查仪器”。只要规则命中，它就能稳定指出问题。例如危险函数、硬编码密钥、不安全的哈希算法、SQL 拼接等。

所以本项目的思路是：

```text
安全扫描工具负责找证据
大模型 Agent 负责解释证据
报告生成模块负责沉淀结果
```

这就是项目比“直接用 AI 看代码”更有工程价值的地方。

## 你现在应该怎么学？

### 第 1 天：看懂项目

阅读这几个文件：

- `README.md`
- `docs/roadmap.md`
- `docs/project-checklist.md`
- `docs/deployment-steps.md`

目标不是全部背下来，而是能说清楚：

- 项目输入是什么？
- 项目输出是什么？
- 中间用了哪些工具？
- 为什么这个项目和安全相关？

### 第 2 天：跑通 GitHub 仓库

你要做的是把本地项目推到 GitHub：

```powershell
cd C:\Users\sz\Documents\Codex\2026-06-29\yu\CodeSec-Agent-Project
git push
```

然后打开：

```text
https://github.com/susz347/CodeSec-Agent
```

确认 README 能正常显示。

### 第 3 天：理解 PR-Agent

先不用改 PR-Agent 源码，只理解它能做什么：

- 自动看 PR
- 自动评论 review
- 支持 `/review`
- 支持 `/improve`
- 支持 `/ask`

第一阶段只需要通过 GitHub Action 跑通它。

### 第 4 天：理解 Semgrep / Bandit

你只需要先知道两条命令：

```bash
semgrep scan --config auto --json -o semgrep-result.json .
```

```bash
bandit -r . -f json -o bandit-result.json
```

这两条命令的意义是：扫描当前项目，并把结果保存成 JSON 文件。

### 第 5 天：理解报告生成

扫描工具输出的是机器友好的 JSON，报告生成要把它变成人能读的 Markdown。

第一版不用复杂，只需要做到：

```text
发现了几个问题
每个问题在哪个文件哪一行
风险等级是什么
为什么危险
怎么修
```

## 你可以先背的 30 秒介绍

> CodeSec-Agent 是一个面向代码安全审计的 Agent 项目。它基于 PR-Agent 做 GitHub PR 自动代码审查，同时接入 Semgrep、Bandit 等静态分析工具发现安全问题。项目会把扫描结果和代码上下文交给大模型分析，生成包含漏洞位置、风险等级、原因解释和修复建议的 Markdown 审计报告。它的重点不是单纯调用大模型，而是把传统静态分析和 Agent 工作流结合起来，提升代码安全审查效率。

## 常见疑问

### 我需要先懂很多安全知识吗？

不需要。第一阶段你只需要懂常见概念，比如输入校验、SQL 注入、命令注入、硬编码密钥、弱加密算法。

后面可以再逐步补 OWASP Top 10 和 CWE Top 25。

### 我需要一开始就做 RAG 吗？

不需要。第一版可以手动整理少量 OWASP/CWE 资料，先生成报告。等 Demo 跑通后，再考虑 RAG。

### 我需要改 PR-Agent 源码吗？

第一阶段不需要。先把 PR-Agent 当成工具用起来，等你理解它的输入输出后，再考虑二次开发。

### 这个项目最终展示什么？

最小展示闭环是：

```text
创建一个有漏洞的测试 PR
-> PR-Agent 自动 Review
-> Semgrep/Bandit 扫描出安全问题
-> CodeSec-Agent 生成 Markdown 审计报告
```

有了这个闭环，就已经可以作为导师双选和简历项目的基础 Demo。
