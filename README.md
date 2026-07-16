# CodeSec-Agent

**CodeSec-Agent** 是一个基于 PR-Agent 改造的代码安全审计与修复建议系统。项目目标不是简单调用大模型做代码点评，而是把 **PR 代码理解、静态安全扫描、漏洞知识库和大模型 Agent 分析** 结合起来，生成可用于工程实践和面试展示的安全审计报告。

## 项目定位

本项目主要面向三个场景：

1. **工程硕导师双选**  
   展示自己在 AI Agent、网络安全、可信软件、关键软件工程方向的兴趣和实践能力。

2. **简历项目**  
   体现 Agent 工作流、静态分析、代码审计、RAG、报告生成等工程能力，避免停留在普通聊天机器人或 PDF 问答项目。

3. **后续求职面试**  
   提供一个可演示、可讲架构、可解释技术取舍的真实项目闭环。

## 核心思路

项目以 [PR-Agent](https://github.com/qodo-ai/pr-agent) 为基础，扩展安全审计能力。

基础能力：

- 使用 PR-Agent 分析 Pull Request 的代码变更、生成 Review 和改进建议。
- 接入 Semgrep、Bandit、npm audit 等静态分析工具，发现潜在安全问题。
- 整理 OWASP、CWE、安全编码规范等资料，作为轻量级漏洞知识库。
- 生成 Markdown / Word 格式的安全审计报告。

整体流程：

```text
Pull Request / 代码仓库
  -> PR-Agent 理解代码变更
  -> Semgrep / Bandit / npm audit 静态扫描
  -> 大模型 Agent 安全分析
  -> 漏洞解释与修复建议
  -> 安全审计报告
```

## 第一阶段 Demo

第一版 Demo 不追求功能复杂，先完成一个可以展示的最小闭环：

1. 创建一个 GitHub 测试仓库。
2. 使用 GitHub Actions 部署 PR-Agent。
3. 创建一个 Pull Request，确认 PR-Agent 能自动生成 Review。
4. 在本地对同一个项目运行 Semgrep / Bandit。
5. 将扫描结果转换成 Markdown 安全审计报告。

## 推荐技术栈

- **代码审查底座**：PR-Agent
- **静态安全扫描**：Semgrep、Bandit、npm audit
- **大模型能力**：OpenAI / Claude / DeepSeek / Gemini 等
- **知识库资料**：OWASP Top 10、CWE Top 25、安全编码规范
- **报告输出**：Markdown，后续可扩展 Word / PDF
- **自动化集成**：GitHub Actions

## 计划功能

- [ ] GitHub PR 自动审查
- [ ] Semgrep 扫描结果解析
- [ ] Bandit 扫描结果解析
- [ ] npm audit 扫描结果解析
- [ ] 安全审计 Prompt 设计
- [ ] 漏洞风险等级归纳
- [ ] 修复建议生成
- [ ] Markdown 报告导出
- [ ] OWASP / CWE 知识库增强
- [ ] Web 页面或可视化面板

## 项目价值

这个项目适合作为软件工程与网络安全交叉方向的展示项目：

- 它靠近 **AI Agent**，而不是普通 RAG 问答。
- 它贴近 **网络安全、可信软件、关键软件工程** 等研究方向。
- 它能展示完整工程闭环：代码输入、扫描分析、Agent 推理、报告输出。
- 它可以逐步扩展，不需要一开始就做成大而全的平台。

## 简历描述示例

**CodeSec-Agent：基于大模型 Agent 的代码安全审计与修复建议系统**

- 基于 PR-Agent 构建 GitHub PR 自动审查流程，实现代码变更理解、审查意见生成和修复建议输出。
- 接入 Semgrep / Bandit 等静态分析工具，提取潜在漏洞、危险函数调用和不安全编码模式。
- 设计安全审计 Prompt，将扫描结果、代码片段和安全规范结合，生成漏洞成因解释、影响分析和修复建议。
- 支持生成 Markdown 审计报告，包含风险等级、代码位置、问题说明、修复方案和参考依据。

## 目录说明

```text
CodeSec-Agent/
  README.md                       # 项目首页
  docs/
    deployment-steps.md           # 部署步骤
    project-checklist.md          # 项目任务清单
    resume-and-interview.md       # 简历与面试材料
    roadmap.md                    # 四周推进路线
  prompts/
    security_review.md            # 安全审计 Prompt
```

## 当前状态

当前仓库处于项目规划与初始文档阶段。下一步目标是先跑通 PR-Agent 的 GitHub Action 自动 Review，再接入 Semgrep / Bandit 完成第一版安全审计 Demo。

