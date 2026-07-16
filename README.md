# CodeSec-Agent

CodeSec-Agent 是一个面向代码安全审计的 Agent 项目。它不是简单地“调用大模型帮我看代码”，而是把 **PR-Agent 的 Pull Request 审查能力**、**Semgrep/Bandit 等静态安全扫描工具**、**OWASP/CWE 安全知识** 和 **大模型解释能力** 组合起来，生成可读、可展示、可继续扩展的代码安全审计报告。

## 项目定位

这个项目适合用来展示三个方向的能力：

- **工程硕导师双选**：贴近 AI Agent、网络安全、可信软件、关键软件工程。
- **简历项目**：比普通聊天机器人或简单 RAG 项目更有工程含量，能讲代码审查、静态分析、Prompt 设计和报告生成。
- **后续找工作**：可以展示一个从代码输入到安全报告输出的完整闭环。

一句话介绍：

> CodeSec-Agent 是一个基于 PR-Agent 改造的代码安全审计与修复建议系统，能够结合 Pull Request 代码变更、静态安全扫描结果和大模型分析，输出漏洞解释、风险等级和修复建议。

## 为什么有 PR 代码审查，还需要安全扫描工具？

PR-Agent 更像一个“会读代码的 AI 审查助手”，擅长理解代码变更、总结 PR、发现明显逻辑问题、提出改进建议。但安全扫描工具更像“规则明确的安全检查仪器”，擅长稳定地发现特定漏洞模式。

两者不是替代关系，而是互补关系：

| 能力 | PR-Agent / LLM 审查 | Semgrep / Bandit 等安全扫描 |
| --- | --- | --- |
| 主要作用 | 理解代码变更，生成自然语言审查意见 | 按规则发现已知风险模式 |
| 优势 | 会解释上下文，能给出更像人的建议 | 稳定、可重复、适合批量扫描 |
| 局限 | 可能漏报、幻觉、输出不稳定 | 不一定懂业务上下文，可能误报 |
| 在本项目中的角色 | 负责解释、归纳、生成修复建议 | 负责提供可靠的安全发现证据 |

举个简单例子：

- PR-Agent 可能会说：“这段代码缺少输入校验，建议补充校验逻辑。”
- Semgrep/Bandit 可能会明确指出：“第 23 行使用了危险函数 `eval`，可能导致代码注入。”
- CodeSec-Agent 要做的是把两者结合起来：先用扫描工具找到具体风险，再让 Agent 解释为什么危险、影响是什么、怎么修。

所以本项目的核心价值不是“又跑了一个扫描工具”，而是：

> 用静态扫描工具提高安全问题发现的稳定性，用大模型提高漏洞解释和修复建议的可读性。

## 核心流程

```text
Pull Request / 代码仓库
  -> PR-Agent 理解代码变更
  -> Semgrep / Bandit / npm audit 扫描安全问题
  -> Agent 结合扫描结果和代码上下文进行分析
  -> 生成漏洞解释、风险等级和修复建议
  -> 输出 Markdown / Word / PDF 审计报告
```

## 四层架构

```text
CodeSec-Agent
├─ PR-Agent 层
│  └─ 读取 PR diff，生成代码审查、改进建议和解释
├─ 静态扫描层
│  └─ 接入 Semgrep、Bandit、npm audit，输出 JSON 结果
├─ Agent 分析层
│  └─ 结合扫描结果、代码片段、OWASP/CWE 知识生成安全解释
└─ 报告生成层
   └─ 输出 Markdown、后续扩展 Word/PDF
```

## 当前阶段

当前仓库处于项目初始化和学习材料阶段，已经包含：

- 项目 README
- 部署步骤
- 四周路线图
- 项目任务清单
- 简历和面试描述
- 安全审查 Prompt 草稿
- 新手学习指南

下一步目标是先完成一个最小闭环 Demo：

```text
PR 输入 -> PR-Agent 自动 Review -> Semgrep/Bandit 扫描 -> Markdown 安全报告
```

## 推荐执行顺序

1. 先把本仓库推送到 GitHub。
2. 创建一个 GitHub 测试仓库。
3. 部署 PR-Agent GitHub Action。
4. 创建一个测试 Pull Request，确认 PR-Agent 自动评论。
5. 本地运行 Semgrep 或 Bandit。
6. 保存扫描 JSON。
7. 写脚本把 JSON 转成 Markdown 报告。
8. 再考虑 RAG、Web 页面、Word/PDF 报告。

## 目录说明

```text
CodeSec-Agent/
  README.md                       # 项目首页
  docs/
    beginner-guide.md             # 面向新手的学习指南
    deployment-steps.md           # 部署步骤
    project-checklist.md          # 项目任务清单
    resume-and-interview.md       # 简历与面试材料
    roadmap.md                    # 四周推进路线
  prompts/
    security_review.md            # 安全审查 Prompt
  push-to-github.ps1              # 本机一键推送脚本
```

## 技术栈

- **代码审查底座**：PR-Agent
- **静态安全扫描**：Semgrep、Bandit、npm audit
- **大模型能力**：OpenAI、Claude、Gemini、DeepSeek 等
- **知识依据**：OWASP Top 10、CWE Top 25、安全编码规范
- **报告输出**：Markdown，后续可扩展 Word/PDF
- **自动化集成**：GitHub Actions

## 第一阶段 Demo 目标

第一阶段不要追求“大而全”，只追求能展示：

- GitHub PR 触发自动审查。
- 安全扫描工具能输出 JSON。
- 项目能把扫描结果整理成 Markdown 报告。
- 报告里包含漏洞位置、风险等级、原因、影响和修复建议。

## 简历描述示例

**CodeSec-Agent：基于大模型 Agent 的代码安全审计与修复建议系统**

基于 PR-Agent 构建代码审查工作流，接入 Semgrep/Bandit 等静态分析工具，并结合 OWASP/CWE 安全知识库生成漏洞解释与修复建议。系统支持 GitHub PR 自动审查、扫描结果解析、风险等级归纳和 Markdown 审计报告导出，提升代码安全审计效率。

## 学习入口

如果你是第一次接触 Agent、PR-Agent 或代码安全审计，建议先阅读：

- [新手学习指南](docs/beginner-guide.md)
- [部署步骤](docs/deployment-steps.md)
- [项目路线图](docs/roadmap.md)
- [项目任务清单](docs/project-checklist.md)
