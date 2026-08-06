# PR-Agent Phase 1/2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the SHA-pinned PR-Agent v0.41.0 GitHub Action and the PyPI-pinned `pr-agent==0.39.0` local CLI with DeepSeek V4 Flash, then verify both paths against one short-lived same-repository pull request created from the updated default branch.

**Architecture:** Keep all non-secret model and review behavior in one root `.pr_agent.toml`. GitHub Actions owns event handling, least-privilege permissions, and repository-secret injection; the local CLI owns only a short-lived process environment containing the DeepSeek key and a repository-scoped GitHub token. No wrapper application, plugin system, database, or scanner integration is introduced in this phase.

**Tech Stack:** GitHub Actions (PR-Agent v0.41.0), local PR-Agent 0.39.0, DeepSeek API, Python 3.12, PowerShell, TOML, YAML, GitHub CLI.

---

> **实施勘误（2026-08-06）：** PyPI 本地版本固定为 `pr-agent==0.39.0`，GitHub Action 固定到 `v0.41.0` 的完整 SHA；两个发布渠道暂时不同。最终 workflow 移除了 `issues: write`，增加同仓库/非 Bot 限制与 15 分钟超时，并让 `synchronize` 仅执行 `/review`。最终共享 TOML 禁用 fallback，并加入用于降低提示注入风险（非绝对隔离）的审查指令。启用 PR 需经用户批准先合并；端到端验证只在更新后的 `main` 上创建短生命周期验证 PR，并从默认分支读取可信配置。实际操作以仓库配置和 `docs/deployment-steps.md` 为准。

## Scope and maintainability guardrails

- `.pr_agent.toml` is the only source of truth for the model and review instructions.
- `.github/workflows/pr-agent.yml` contains only triggers, permissions, action version, behavior toggles, and secret wiring.
- `docs/deployment-steps.md` is the only detailed deployment guide; `README.md` links to it instead of duplicating commands.
- No API key, PAT, `.env`, virtual environment, generated log, or local PR-Agent secret file is committed.
- Each committed file has one responsibility, and each commit is independently reviewable.
- Phase 3 scanner work must not leak into this plan.

## File map

- Create `.gitignore`: local-secret, virtual-environment, and generated-file exclusions only.
- Create `.pr_agent.toml`: shared, non-secret PR-Agent configuration.
- Create `.github/workflows/pr-agent.yml`: automatic same-repository PR review.
- Modify `docs/deployment-steps.md`: authoritative DeepSeek-based Phase 1/2 instructions and troubleshooting.
- Modify `README.md`: replace duplicated setup commands with a short pointer to the authoritative guide.
- Use `.venv/` locally: untracked Python environment containing `pr-agent==0.39.0`.

### Task 1: Create an isolated implementation branch

**Files:**
- Inspect: repository worktree and `docs/superpowers/specs/2026-08-06-pr-agent-phase1-2-design.md`
- No file changes

- [ ] **Step 1: Verify the starting state**

Run:

```powershell
git status --short
git branch --show-current
git log -2 --oneline
```

Expected:

- Worktree output is empty.
- Current branch is `main`.
- The latest commits include the approved design and this implementation plan.

- [ ] **Step 2: Create the implementation branch**

Run:

```powershell
git switch -c codex/pr-agent-phase1-2
```

Expected: `Switched to a new branch 'codex/pr-agent-phase1-2'`.

- [ ] **Step 3: Confirm isolation**

Run:

```powershell
git branch --show-current
git status --short
```

Expected: branch is `codex/pr-agent-phase1-2` and the worktree is empty.

### Task 2: Protect local credentials and generated state

**Files:**
- Create: `.gitignore`
- Test: PowerShell assertions and `git check-ignore`

- [ ] **Step 1: Run the failing guardrail check**

Run:

```powershell
if (-not (Test-Path -LiteralPath '.gitignore')) { throw '.gitignore is missing' }
```

Expected: command fails with `.gitignore is missing`.

- [ ] **Step 2: Create the minimal ignore file**

Create `.gitignore` with exactly:

```gitignore
# Python local environment
.venv/
__pycache__/
*.py[cod]

# Local credentials
.env
.env.*
pr_agent/settings/.secrets.toml

# Local PR-Agent output
*.log
```

- [ ] **Step 3: Verify the guardrails**

Run:

```powershell
New-Item -ItemType Directory -Path '.venv' -Force | Out-Null
New-Item -ItemType File -Path '.env' -Force | Out-Null
git check-ignore --quiet -- '.venv'
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment is not ignored' }
git check-ignore --quiet -- '.env'
if ($LASTEXITCODE -ne 0) { throw 'Local credential file is not ignored' }
git status --short
```

Expected: `.gitignore` is the only untracked file; `.venv` and `.env` are absent from status.

- [ ] **Step 4: Remove the empty validation-only `.env` file**

Run:

```powershell
Remove-Item -LiteralPath '.env'
```

Expected: `.env` no longer exists; `.venv/` remains for the later Python installation.

- [ ] **Step 5: Verify and commit**

Run:

```powershell
git diff --check
git add -- '.gitignore'
git diff --cached --check
git commit -m "chore: protect local PR-Agent credentials"
```

Expected: one commit containing only `.gitignore`.

### Task 3: Install and smoke-test the pinned local CLI

**Files:**
- Local only: `.venv/`
- No committed file changes

- [ ] **Step 1: Verify Python 3.12**

Run:

```powershell
py -3.12 --version
```

Expected: `Python 3.12.x`. If the launcher cannot find Python 3.12, install it before continuing.

- [ ] **Step 2: Create or refresh the virtual environment**

Run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Expected: both commands exit `0` and all installed files remain under ignored `.venv/`.

- [ ] **Step 3: Install the exact PR-Agent version**

Run:

```powershell
.\.venv\Scripts\python.exe -m pip install pr-agent==0.39.0
```

Expected: installation exits `0` and reports `Successfully installed` or `Requirement already satisfied` for `pr-agent==0.39.0`.

- [ ] **Step 4: Verify the installed package and executable**

Run:

```powershell
.\.venv\Scripts\python.exe -c "from importlib.metadata import version; assert version('pr-agent') == '0.39.0'; print(version('pr-agent'))"
.\.venv\Scripts\pr-agent.exe --help
```

Expected: first command prints `0.39.0`; second command exits `0` and displays PR-Agent CLI usage.

- [ ] **Step 5: Confirm that local installation did not dirty Git**

Run:

```powershell
git status --short
```

Expected: empty output.

### Task 4: Add the shared non-secret PR-Agent configuration

**Files:**
- Create: `.pr_agent.toml`
- Test: Python `tomllib` assertions and credential-pattern scan

- [ ] **Step 1: Run the failing configuration check**

Run:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; assert Path('.pr_agent.toml').is_file(), '.pr_agent.toml is missing'"
```

Expected: assertion fails because `.pr_agent.toml` does not exist.

- [ ] **Step 2: Create the shared configuration**

Create `.pr_agent.toml` with exactly:

```toml
[config]
model = "deepseek/deepseek-v4-flash"

[pr_reviewer]
extra_instructions = """
重点审查本次 Pull Request 引入的安全风险，包括输入校验、命令注入、SQL 注入、路径遍历、身份认证、权限控制、敏感信息泄露、不安全加密和依赖使用风险。
每条结论必须引用具体变更或代码证据，并明确区分确认问题、可疑问题和可能误报。
不要提供漏洞利用步骤；优先给出最小、可验证的防御性修复建议。
"""
```

- [ ] **Step 3: Parse and assert the configuration**

Run:

```powershell
.\.venv\Scripts\python.exe -c "import tomllib; from pathlib import Path; data=tomllib.loads(Path('.pr_agent.toml').read_text(encoding='utf-8')); assert data['config']['model']=='deepseek/deepseek-v4-flash'; assert '确认问题' in data['pr_reviewer']['extra_instructions']; print('TOML OK')"
```

Expected: prints `TOML OK` and exits `0`.

- [ ] **Step 4: Check that the shared configuration contains no credential**

Run:

```powershell
$matches = Select-String -LiteralPath '.pr_agent.toml' -Pattern 'sk-[A-Za-z0-9_-]{16,}|github_pat_[A-Za-z0-9_]+' -AllMatches
if ($matches) { throw 'A credential-like value was found in .pr_agent.toml' }
```

Expected: no output and exit `0`.

- [ ] **Step 5: Verify and commit**

Run:

```powershell
git diff --check
git add -- '.pr_agent.toml'
git diff --cached --check
git commit -m "config: share DeepSeek PR-Agent review settings"
```

Expected: one commit containing only `.pr_agent.toml`.

### Task 5: Add the least-privilege GitHub Action

**Files:**
- Create: `.github/workflows/pr-agent.yml`
- Test: YAML parse, semantic text assertions, and credential-pattern scan

- [ ] **Step 1: Run the failing workflow check**

Run:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; assert Path('.github/workflows/pr-agent.yml').is_file(), 'workflow is missing'"
```

Expected: assertion fails because the workflow does not exist.

- [ ] **Step 2: Create the workflow**

Create `.github/workflows/pr-agent.yml` with exactly:

```yaml
name: PR Agent Security Review

on:
  pull_request:
    types: [opened, reopened, ready_for_review, synchronize]

permissions:
  contents: read
  issues: write
  pull-requests: write

jobs:
  review:
    if: ${{ github.event.sender.type != 'Bot' }}
    runs-on: ubuntu-latest
    steps:
      - name: Run PR-Agent
        uses: the-pr-agent/pr-agent@570f67ed5fc8db5be74c18df070bc20079b64b0d # v0.41.0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          github_action_config.auto_review: "true"
          github_action_config.auto_describe: "false"
          github_action_config.auto_improve: "false"
```

- [ ] **Step 3: Parse the YAML syntax**

Run:

```powershell
.\.venv\Scripts\python.exe -c "import yaml; from pathlib import Path; data=yaml.safe_load(Path('.github/workflows/pr-agent.yml').read_text(encoding='utf-8')); assert data['name']=='PR Agent Security Review'; assert 'jobs' in data; print('YAML OK')"
```

Expected: prints `YAML OK`. `pr-agent==0.39.0` supplies the YAML dependency used for this syntax check.

- [ ] **Step 4: Verify security-sensitive workflow invariants**

Run:

```powershell
$workflow = Get-Content -LiteralPath '.github/workflows/pr-agent.yml' -Raw
$required = @(
  'the-pr-agent/pr-agent@570f67ed5fc8db5be74c18df070bc20079b64b0d',
  'contents: read',
  'issues: write',
  'pull-requests: write',
  'secrets.DEEPSEEK_API_KEY'
)
foreach ($item in $required) {
  if (-not $workflow.Contains($item)) { throw "Missing workflow invariant: $item" }
}
foreach ($forbidden in @('pull_request_target', 'contents: write', 'checks: write', 'issue_comment')) {
  if ($workflow.Contains($forbidden)) { throw "Forbidden workflow capability: $forbidden" }
}
```

Expected: no output and exit `0`.

- [ ] **Step 5: Verify no literal credential is present**

Run:

```powershell
$matches = Select-String -LiteralPath '.github/workflows/pr-agent.yml' -Pattern 'sk-[A-Za-z0-9_-]{16,}|github_pat_[A-Za-z0-9_]+' -AllMatches
if ($matches) { throw 'A credential-like value was found in the workflow' }
```

Expected: no output and exit `0`.

- [ ] **Step 6: Verify and commit**

Run:

```powershell
git diff --check
git add -- '.github/workflows/pr-agent.yml'
git diff --cached --check
git commit -m "ci: add DeepSeek PR-Agent review"
```

Expected: one commit containing only the workflow.

### Task 6: Make deployment documentation authoritative and non-duplicative

**Files:**
- Modify: `docs/deployment-steps.md`
- Modify: `README.md`
- Test: documentation assertions and stale-command scan

- [ ] **Step 1: Run the failing stale-documentation check**

Run:

```powershell
$stale = Select-String -Path 'README.md','docs/deployment-steps.md' -Pattern 'qodo-ai/pr-agent@main|OPENAI_KEY|\$env:OPENAI_KEY' -AllMatches
if ($stale.Count -gt 0) { throw "Found $($stale.Count) stale deployment references" }
```

Expected: command fails because the current documentation still contains the old action namespace and OpenAI-only examples.

- [ ] **Step 2: Replace `docs/deployment-steps.md` with the authoritative Phase 1/2 guide**

Use this structure and exact operational values:

> Historical draft retained as plan context; this fenced example is non-executable and is superseded by Tasks 8–12 plus the current `docs/deployment-steps.md` bootstrap sequence.

```markdown
# 部署与运行步骤

本文记录 CodeSec-Agent 的分阶段部署方法。本轮已实施 Phase 1 和 Phase 2；后续扫描与报告阶段仍属于待开发范围。

## Phase 1：使用 GitHub Actions 运行 PR-Agent

### 前置条件

- GitHub 仓库 `susz347/CodeSec-Agent`。
- 可用的 DeepSeek API Key。
- 仓库根目录已提交 `.pr_agent.toml`。
- Workflow 使用固定的 PR-Agent `0.41.0` 提交。

### 配置 GitHub Secret

进入：

```text
Settings → Secrets and variables → Actions → New repository secret
```

创建：

```text
Name: DEEPSEEK_API_KEY
Secret: 你的 DeepSeek API Key
```

不要把 Key 写进 workflow、`.pr_agent.toml`、`.env` 或 Git 历史。`GITHUB_TOKEN` 由 GitHub Actions 自动提供。

### Workflow

实际配置位于 `.github/workflows/pr-agent.yml`。它只监听同仓库的 Pull Request，并使用以下模型配置：

```text
deepseek/deepseek-v4-flash
```

首版仅运行 review，不监听 `issue_comment`，也不使用 `pull_request_target`。

### 验证

1. 从当前仓库创建测试分支。
2. 提交 `.pr_agent.toml`、workflow 或文档变更。
3. 创建 Pull Request。
4. 在 Actions 中确认 `PR Agent Security Review` 成功。
5. 在 PR 中确认出现自动审查评论。
6. 检查日志，确认没有密钥内容。

## Phase 2：本地运行 PR-Agent CLI

### 创建 Python 3.12 虚拟环境

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pr-agent==0.39.0
.\.venv\Scripts\pr-agent.exe --help
```

### 创建 GitHub Fine-grained PAT

在 GitHub 的 Developer settings 中创建 Fine-grained personal access token：

- Repository access：仅 `susz347/CodeSec-Agent`。
- Contents：Read。
- Pull requests：Read and write。
- Issues：Read and write。
- 建议有效期：30 天。

不要把 Token 发送到对话或写入仓库。

### 在当前 PowerShell 会话注入凭据

```powershell
$deepSeekSecret = Read-Host 'DeepSeek API Key' -AsSecureString
$githubSecret = Read-Host 'GitHub Fine-grained PAT' -AsSecureString
$env:DEEPSEEK_API_KEY = [System.Net.NetworkCredential]::new('', $deepSeekSecret).Password
$env:GITHUB__USER_TOKEN = [System.Net.NetworkCredential]::new('', $githubSecret).Password
```

### 执行 review

先在测试 PR 页面复制完整 URL，然后执行：

```powershell
$prUrl = Read-Host '测试 PR 的完整 URL'
.\.venv\Scripts\pr-agent.exe --pr_url $prUrl review
```

### 清理当前会话凭据

```powershell
Remove-Item Env:DEEPSEEK_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:GITHUB__USER_TOKEN -ErrorAction SilentlyContinue
$deepSeekSecret = $null
$githubSecret = $null
```

## 常见问题

### DeepSeek 返回 401

Key 无效、已撤销或没有正确注入。重新设置 Secret 或当前 PowerShell 环境变量，不要打印 Key。

### DeepSeek 返回 402

检查 DeepSeek 账户余额和计费状态。

### DeepSeek 返回 429

请求频率达到限制。等待后重试，避免反复更新 PR。

### GitHub 返回 403

检查 workflow 的 `permissions`，或检查 Fine-grained PAT 是否仅对目标仓库授予了 Contents read、Pull requests read/write 和 Issues read/write。

### Fork PR 没有运行

这是首版的安全边界。不要为了读取 Secret 随意改成 `pull_request_target`。

### 找不到模型

确认 `.pr_agent.toml` 中使用的是 `deepseek/deepseek-v4-flash`，而不是已经弃用的 `deepseek-chat`。

## 后续阶段

- Phase 3：Semgrep、Bandit 和 npm audit。
- Phase 4：统一 finding、Agent 分析和 Markdown 报告。
```

- [ ] **Step 3: Replace the duplicated README quick-start body**

Under `## 快速开始`, replace the detailed workflow and scanner commands with:

```markdown
## 快速开始

项目按阶段实施：

1. 使用 GitHub Actions 运行 PR-Agent。
2. 在本地运行 PR-Agent CLI。
3. 运行 Semgrep、Bandit 和 npm audit。
4. 解析扫描结果并生成安全审计报告。

当前部署配置、DeepSeek 接入方式、凭据权限和验证命令统一维护在 [部署与运行步骤](docs/deployment-steps.md) 中，README 不重复保存容易过期的 workflow 和命令副本。
```

Keep the later `## 开发路线` and all subsequent sections unchanged.

- [ ] **Step 4: Verify documentation consistency**

Run:

```powershell
$stale = Select-String -Path 'README.md','docs/deployment-steps.md' -Pattern 'qodo-ai/pr-agent@main|OPENAI_KEY|\$env:OPENAI_KEY' -AllMatches
if ($stale) { throw 'Stale OpenAI-only or mutable-action documentation remains' }
$required = @('DEEPSEEK_API_KEY','deepseek/deepseek-v4-flash','pr-agent==0.39.0','GITHUB__USER_TOKEN')
$deployment = Get-Content -LiteralPath 'docs/deployment-steps.md' -Raw
foreach ($item in $required) {
  if (-not $deployment.Contains($item)) { throw "Deployment guide is missing: $item" }
}
```

Expected: no output and exit `0`.

- [ ] **Step 5: Verify and commit**

Run:

```powershell
git diff --check
git add -- 'README.md' 'docs/deployment-steps.md'
git diff --cached --check
git commit -m "docs: document DeepSeek PR-Agent deployment"
```

Expected: one documentation-only commit.

### Task 7: Run the complete local static verification suite

**Files:**
- Verify: `.gitignore`
- Verify: `.pr_agent.toml`
- Verify: `.github/workflows/pr-agent.yml`
- Verify: `README.md`
- Verify: `docs/deployment-steps.md`

- [ ] **Step 1: Verify TOML and YAML parsing**

Run:

```powershell
.\.venv\Scripts\python.exe -c "import tomllib, yaml; from pathlib import Path; tomllib.loads(Path('.pr_agent.toml').read_text(encoding='utf-8')); yaml.safe_load(Path('.github/workflows/pr-agent.yml').read_text(encoding='utf-8')); print('CONFIG PARSE OK')"
```

Expected: prints `CONFIG PARSE OK`.

- [ ] **Step 2: Verify the pinned CLI and action versions**

Run:

```powershell
.\.venv\Scripts\python.exe -c "from importlib.metadata import version; assert version('pr-agent') == '0.39.0'; print('CLI 0.39.0 OK')"
$workflow = Get-Content -LiteralPath '.github/workflows/pr-agent.yml' -Raw
if (-not $workflow.Contains('the-pr-agent/pr-agent@570f67ed5fc8db5be74c18df070bc20079b64b0d')) { throw 'Action is not pinned to the approved commit' }
```

Expected: prints `CLI 0.39.0 OK` and exits `0`.

- [ ] **Step 3: Scan tracked and untracked project files for credential-like values**

Run:

```powershell
$files = Get-ChildItem -Recurse -Force -File | Where-Object {
  $_.FullName -notmatch '\\.git\\|\\.venv\\'
}
$matches = $files | Select-String -Pattern 'sk-[A-Za-z0-9_-]{16,}|github_pat_[A-Za-z0-9_]+' -AllMatches
if ($matches) { $matches; throw 'Credential-like value found in project files' }
```

Expected: no matches and exit `0`.

- [ ] **Step 4: Verify whitespace, scope, and worktree state**

Run:

```powershell
git diff --check
git status --short
git log --oneline main..HEAD
```

Expected:

- `git diff --check` exits `0`.
- Worktree is empty.
- Branch contains small commits for ignore rules, shared config, workflow, and documentation.

### Task 8: Publish and merge the enabling PR before adding credentials

**Files:**
- GitHub branch: `codex/pr-agent-phase1-2`
- Enabling pull request targeting `main`
- No credential changes

- [ ] **Step 1: Push the implementation branch and create the enabling PR**

Push `codex/pr-agent-phase1-2`, then create a PR targeting `main`. This first PR installs the workflow and trusted configuration; it is not the end-to-end validation PR. Do not attempt to make the Action read `.pr_agent.toml` from the PR head.

- [ ] **Step 2: Complete static and human review**

Verify the branch diff, configuration parsing, SHA pin, permissions, credential scan, and documentation. The Action may not run because the workflow is not yet present on the default branch; that is expected and is not a failed deployment test.

- [ ] **Step 3: Request explicit user approval and merge**

Report the exact diff and static verification. Do not merge until the user explicitly approves. After approval, merge the enabling PR so `.github/workflows/pr-agent.yml` and `.pr_agent.toml` become trusted default-branch content.

### Task 9: Configure credentials after the enabling PR is merged

**Files:**
- GitHub Repository Secret: `DEEPSEEK_API_KEY`
- GitHub user setting: short-lived Fine-grained PAT
- No repository file changes

- [ ] **Step 1: Confirm the external-data boundary**

PR diff, title, description, comments, and related code context are sent to DeepSeek during review. Before adding a Secret for a private or commercial repository, confirm organizational data-processing and third-party-model policy. The first validation PR must contain no secrets, customer data, or production data.

- [ ] **Step 2: Add the DeepSeek Repository Secret manually**

Create `DEEPSEEK_API_KEY` under repository **Settings → Secrets and variables → Actions**. Do not paste its value into chat, command transcripts, logs, or repository files.

- [ ] **Step 3: Create the repository-scoped Fine-grained PAT manually**

Use a 30-day-or-shorter Fine-grained PAT restricted to `susz347/CodeSec-Agent`, with `Contents: Read-only` and `Pull requests: Read and write`. Store it in a password manager and do not put it in Git credential configuration or any project file.

- [ ] **Step 4: Confirm names and scopes only**

Expected confirmation contains only that `DEEPSEEK_API_KEY` exists and the PAT is repository-scoped with the required permissions. Never request or display either secret value.

### Task 10: Create a short-lived validation PR from updated main

**Files:**
- Temporary same-repository validation branch
- One non-sensitive probe change that will not be merged

- [ ] **Step 1: Start from the updated default branch**

Update local `main` after the enabling PR merge, then create a uniquely named short-lived validation branch. Confirm the branch contains the merged workflow and `.pr_agent.toml` before adding a probe.

- [ ] **Step 2: Add a non-sensitive probe and open the validation PR**

Use a small disposable documentation or test fixture change containing no secrets, customer data, or production data. Open a same-repository PR targeting `main`; do not use a Fork. Record the validation PR URL for both Action and local CLI checks.

- [ ] **Step 3: Confirm trusted configuration origin**

The validation branch originates from the updated `main`. The Action and formal CLI validation use the reviewed `.pr_agent.toml` on the default branch, not a PR-head override. Do not use `--config-branch codex/pr-agent-phase1-2` for this validation.

### Task 11: Verify the Action and local CLI on the same validation PR

**Files:**
- Read-only workflow/log inspection
- Process-local environment variables only

- [ ] **Step 1: Verify Phase 1 in GitHub**

In the validation PR **Checks** or repository **Actions** page, confirm `PR Agent Security Review` succeeds and publishes a review. Push one additional disposable probe commit and confirm `synchronize` runs only `/review`. Verify logs do not expose credentials; do not copy full logs into public comments.

- [ ] **Step 2: Inject credentials only in the user's PowerShell**

Use `Read-Host -AsSecureString` to populate process-local `DEEPSEEK_API_KEY` and `GITHUB__USER_TOKEN`. Do not send values to chat or write them to files.

- [ ] **Step 3: Verify Phase 2 using trusted default-branch configuration**

Run against the same validation PR:

```powershell
.\.venv\Scripts\pr-agent.exe --pr_url $prUrl --config-branch main review
```

Expected: the CLI exits `0`, publishes a second review, and uses `.pr_agent.toml` from `main`. Before the enabling PR merge, `--config-branch codex/pr-agent-phase1-2` may be used only for an explicitly accepted maintainer precheck; it is forbidden for the Action and does not count as formal validation.

- [ ] **Step 4: Clear credentials immediately**

Remove both environment variables, clear the temporary secure-string variables, and assert that `Env:DEEPSEEK_API_KEY` and `Env:GITHUB__USER_TOKEN` no longer exist.

### Task 12: Close the validation PR and remove temporary state

**Files:**
- Validation PR and branch
- Temporary probe files and local environment only

- [ ] **Step 1: Capture final evidence**

Record the enabling PR merge, validation PR URL, successful Action result, successful local CLI result, installed `pr-agent==0.39.0`, trusted `main` config branch, credential cleanup, and absence of literal credentials in logs. Do not include secret values or full logs.

- [ ] **Step 2: Close without merging the validation PR**

The validation PR contains disposable probes and must not be merged. Close it after both paths pass.

- [ ] **Step 3: Delete validation branches and probes**

Delete the remote and local validation branches. Remove all temporary probe files and generated logs. Confirm no probe commit or file entered `main`.

- [ ] **Step 4: Verify final cleanliness**

Confirm the normal worktree is clean, the temporary environment variables are absent, and the short-lived PAT is revoked if no longer needed. Remove the implementation worktree/merged branch only after the enabling PR has merged and cleanup is safe.

## Completion evidence

Do not claim Phase 1 or Phase 2 complete without all of the following fresh evidence:

- Local TOML and YAML parse commands exit `0`.
- Installed local PR-Agent version is exactly `0.39.0`; the Action remains pinned to the approved v0.41.0 SHA.
- Credential-pattern scan finds no repository secret.
- User explicitly approved and merged the enabling PR before credentials and end-to-end validation were used.
- The short-lived validation PR was created from the updated `main`, and formal Action/CLI runs used trusted default-branch configuration.
- GitHub Action check succeeds on the validation PR.
- Action-generated review comment exists.
- Local CLI command with `--config-branch main` exits `0` against the same validation PR.
- Local-CLI-generated review output exists.
- `DEEPSEEK_API_KEY` and `GITHUB__USER_TOKEN` are removed from the local process environment.
- The validation PR is closed without merging; remote/local validation branches and temporary probes are deleted.
