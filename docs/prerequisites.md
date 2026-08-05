# 前置知识

本文整理理解和开发 CodeSec-Agent 所需的基础知识。读者不需要一次性掌握全部内容，但建议先了解每个概念在系统中的作用。

## 1. Git 与 Pull Request

Git 用于管理代码版本。Pull Request，简称 PR，是一次等待审查和合并的代码变更。

PR 审查系统通常关注：

- 本次改了哪些文件。
- 哪些代码被新增、删除或修改。
- 变更是否引入风险。
- 是否需要补充测试或修复建议。

在 CodeSec-Agent 中，PR 是重要输入之一。PR-Agent 会读取 PR diff，并生成代码审查上下文。

## 2. GitHub Actions

GitHub Actions 是 GitHub 提供的 CI/CD 自动化能力。它可以在 PR 创建、代码推送或评论触发时运行任务。

本项目使用 GitHub Actions 完成两类自动化：

- 触发 PR-Agent 自动审查。
- 运行安全扫描并保存报告产物。

需要理解的关键词：

- `workflow`：自动化流程文件。
- `job`：一次流程中的任务。
- `step`：任务中的具体执行步骤。
- `secret`：用于保存 API Key 等敏感配置。

## 3. PR-Agent

PR-Agent 是开源 AI code review agent。它可以分析 Pull Request，并生成 review、改进建议和问答回复。

本项目将 PR-Agent 作为 PR 审查底座，重点使用它获取代码变更上下文，而不是从零实现一个 PR 审查机器人。

常见能力包括：

- `/review`：生成代码审查意见。
- `/improve`：生成改进建议。
- `/ask`：围绕 PR 内容进行问答。

## 4. 静态应用安全测试

静态应用安全测试，常称 SAST，是在不运行程序的情况下分析源代码、配置文件或依赖信息的安全测试方式。

SAST 适合发现：

- 危险函数调用。
- 输入校验缺失。
- SQL 拼接风险。
- 命令注入风险。
- 硬编码密钥。
- 弱加密算法。
- 已知依赖漏洞。

本项目第一阶段关注 Semgrep、Bandit 和 npm audit。

## 5. Semgrep

Semgrep 是通用静态分析工具。它通过规则匹配代码模式，支持多种语言。

在 CodeSec-Agent 中，Semgrep 用于发现跨语言的常见安全风险，并输出 JSON 结果供后续解析。

典型输出信息包括：

- 规则 ID。
- 文件路径。
- 起止行号。
- 风险描述。
- 严重等级。

## 6. Bandit

Bandit 是 Python 代码安全扫描工具。它可以发现 Python 项目中的常见风险，例如不安全的函数调用、弱随机数、硬编码密码等。

在 CodeSec-Agent 中，Bandit 用于补充 Python 项目的安全扫描能力。

## 7. npm audit

npm audit 用于检查 Node.js 项目的依赖漏洞。它会根据依赖树和漏洞数据库判断是否存在已知安全问题。

在 CodeSec-Agent 中，npm audit 主要用于依赖安全分析，而 Semgrep 和 Bandit 更偏向源代码扫描。

## 8. OWASP 与 CWE

OWASP 是开放 Web 应用安全项目，常见资料包括 OWASP Top 10。它适合帮助理解 Web 应用中的高频安全风险。

CWE 是通用弱点枚举，用于描述软件缺陷和漏洞类型。例如输入验证不当、命令注入、路径遍历等。

在本项目中，OWASP 和 CWE 用作安全解释的参考依据。

## 9. 大模型与 Agent

大模型擅长自然语言理解和生成，但不应单独作为安全结论来源。它可能漏报、误判或生成没有证据的结论。

Agent 层在本项目中的职责是：

- 读取扫描器结果。
- 结合代码片段解释问题。
- 归纳风险等级和影响。
- 生成修复建议。
- 明确区分确认问题和可疑问题。

## 10. JSON 与 Markdown

扫描器通常输出 JSON，因为它结构化、便于程序解析。

审计报告使用 Markdown，因为它可读性好，适合在 GitHub、文档系统和 CI 产物中展示。

CodeSec-Agent 的一个核心转换过程就是：

```text
扫描器 JSON
  -> 统一 finding 结构
  -> Agent 安全分析
  -> Markdown 审计报告
```

## 建议学习顺序

1. 先理解 Git、PR 和 GitHub Actions。
2. 再理解 PR-Agent 的输入和输出。
3. 接着学习 Semgrep、Bandit、npm audit 的基本命令。
4. 然后理解 OWASP/CWE 的作用。
5. 最后再看 Agent 分析和报告生成。
