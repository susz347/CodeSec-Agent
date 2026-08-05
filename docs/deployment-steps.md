# 部署与运行步骤

本文说明 CodeSec-Agent 第一阶段所需的运行方式，包括 PR-Agent GitHub Action、本地 PR-Agent CLI、Semgrep、Bandit 和 npm audit。

## 前置条件

运行第一阶段 Demo 前，需要准备：

- GitHub 账号。
- 一个用于测试的 GitHub 仓库。
- 一个可用的大模型 API Key，例如 OpenAI、Claude、Gemini、DeepSeek 等。
- Git 和 Python 环境。
- 可选：Docker，用于运行 Semgrep 容器版本。

## Phase 1: 使用 GitHub Actions 运行 PR-Agent

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

然后在 GitHub 仓库中添加 Secret：

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

添加：

```text
OPENAI_KEY = your_api_key
```

`GITHUB_TOKEN` 由 GitHub Actions 自动提供，不需要手动创建。

## 验证 PR-Agent

1. 新建一个分支。
2. 提交一处小的代码变更。
3. 创建 Pull Request。
4. 查看 Actions 是否成功运行。
5. 查看 PR 下是否出现 PR-Agent 的审查评论。

验证通过后，说明 PR 审查入口已经跑通。

## Phase 2: 本地运行 PR-Agent CLI

本地 CLI 适合后续调试和二次开发。

安装：

```bash
pip install pr-agent
```

在 Windows PowerShell 设置 API Key：

```powershell
$env:OPENAI_KEY="your_api_key"
```

对指定 PR 执行 review：

```bash
pr-agent --pr_url https://github.com/owner/repo/pull/123 review
```

## Phase 3: 运行静态安全扫描

### Semgrep

基础命令：

```bash
semgrep scan --config auto --json -o semgrep-result.json .
```

Windows Docker 示例：

```bash
docker run --rm -v "%cd%:/src" semgrep/semgrep semgrep scan --config auto --json -o /src/semgrep-result.json /src
```

### Bandit

Bandit 适用于 Python 项目：

```bash
pip install bandit
bandit -r . -f json -o bandit-result.json
```

### npm audit

npm audit 适用于 Node.js 项目：

```bash
npm audit --json > npm-audit-result.json
```

## Phase 4: 生成安全审计报告

第一版报告可以先基于扫描器 JSON 文件生成 Markdown。

最小字段建议：

- 项目名称。
- 扫描时间。
- 扫描器名称。
- 漏洞文件和行号。
- 风险等级。
- 问题原因。
- 潜在影响。
- 修复建议。
- CWE、OWASP 或安全编码规范参考。

## 常见问题

### GitHub 页面没有更新

如果本地已经提交但 GitHub 没有变化，通常是还没有执行 `git push`。在本机 PowerShell 中运行：

```powershell
git push
```

### Codex 无法直接推送 GitHub

Codex 环境可能无法读取本机 GitHub 凭据。推荐由 Codex 完成文件修改和 commit，再由本机 PowerShell 执行 `git push`。

### 扫描器没有发现问题

这不一定代表项目完全安全。可能原因包括：测试代码没有典型漏洞、规则集覆盖不足、语言不匹配或扫描路径不正确。
