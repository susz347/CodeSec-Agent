# 部署与运行步骤

本文是 CodeSec-Agent 的唯一详细部署入口。本项目可概括为四个部署里程碑：

1. **Phase 1：GitHub Actions PR-Agent**（已完成端到端验证）。
2. **Phase 2：本地 PR-Agent CLI**（已完成端到端验证）。
3. **Phase 3：静态安全扫描与结果归一化**（Semgrep-first 切片已完成验证）。
4. **Phase 4：Agent 分析、报告与自动化**（本地五格式报告、确定性分析与 PR 摘要切片已完成）。

完整研发阶段、任务与交付物统一见 [项目路线图](roadmap.md)。Phase 3 的 Semgrep、Bandit 与 npm audit 已作为独立适配器完成本地验证。

## 版本与安全边界

- 共享配置位于仓库根目录的 [`.pr_agent.toml`](../.pr_agent.toml)，模型为 `deepseek/deepseek-v4-flash`。
- GitHub Action 固定到 PR-Agent `v0.41.0` 对应的完整提交 SHA `570f67ed5fc8db5be74c18df070bc20079b64b0d`。
- 本地 CLI 固定安装 PyPI 可用的 `pr-agent==0.39.0`。Action 与 PyPI 当前发布渠道不同，版本号暂时不一致；不要自行把其中一端改成浮动版本。
- 共享 TOML 通过 `fallback_models = []` 禁用备用模型，避免 DeepSeek 失败时把代码发送给其他提供商；审查指令同时要求把 PR 描述、代码、注释和字符串视为不可信数据，以降低提示注入风险，但这不是绝对隔离，不能替代人工复核。
- 密钥只进入 GitHub Repository Secret 或用户自己的当前 PowerShell 进程，不写入文件、Git 历史或聊天。

## Phase 1：GitHub Actions PR-Agent

### 1. 先合并启用 PR

包含 workflow 和 `.pr_agent.toml` 的首个 PR 只是“启用 PR”，不作为端到端验证对象。GitHub Action 不应从 PR head 读取分支可控配置后接触仓库 Secret；本项目只让 Action 和正式本地验证读取默认分支 `main` 上已经审核的 `.pr_agent.toml`。

先完成启用 PR 的静态检查和人工审查，再等待用户明确批准合并。未经用户批准不得合并。启用 PR 合并后，才继续配置凭据并创建验证 PR。

### 2. 确认数据外发边界，再配置 DeepSeek Secret

运行 review 时，PR diff、标题、描述、评论和相关代码上下文会发送给 DeepSeek。私有或商业仓库应先确认组织的数据处理、保密和第三方模型政策。首次验证只能使用不含密钥、客户数据、生产数据或其他敏感信息的测试 PR。

需要一个可用的 DeepSeek API Key。进入目标 GitHub 仓库：

```text
Settings → Secrets and variables → Actions → New repository secret
```

创建名为 `DEEPSEEK_API_KEY` 的 Repository Secret，并将 Key 作为 Secret 值。不要在聊天、截图、日志或仓库文件中展示该值。`GITHUB_TOKEN` 由 GitHub Actions 自动提供，不需要自行创建。

### 3. 确认 Workflow 的行为

实际配置见 [`.github/workflows/pr-agent.yml`](../.github/workflows/pr-agent.yml)，不要在本文复制维护第二份 workflow。当前边界如下：

- 监听 `opened`、`reopened`、`ready_for_review` 和 `synchronize`。
- 新建或重新进入可审查状态时自动 review；`synchronize`（向 PR 推送新提交）只执行 `/review`，不执行 describe 或 improve。
- 跳过 Bot 触发的事件，也跳过来自 Fork 的 PR，避免向不受信任上下文暴露 Secret。
- 不监听 `issue_comment`，不使用 `pull_request_target`。
- 权限仅为 `contents: read` 和 `pull-requests: write`。
- 单次任务最多运行 15 分钟。

### 4. 创建短生命周期验证 PR

确认启用 PR 已经用户批准并合并，且 `.pr_agent.toml`、workflow 和 Secret 均已在目标仓库就绪。以下命令必须从仓库根目录运行，并要求 [GitHub CLI](https://cli.github.com/) 已安装且完成认证。

验证探针只包含说明文字，不得包含密钥、客户数据、生产数据、真实漏洞或漏洞利用步骤。固定验证分支和探针文件会在验证后随未合并分支一起删除，绝不合并到 `main`。

```powershell
$ErrorActionPreference = 'Stop'
$repoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) { throw '当前目录不是 Git 仓库' }
if ((Resolve-Path '.').Path -ne (Resolve-Path $repoRoot).Path) { throw '请先切换到仓库根目录' }
Get-Command gh -ErrorAction Stop | Out-Null
gh auth status
if ($LASTEXITCODE -ne 0) {
  Write-Host 'GitHub CLI 尚未认证，即将打开浏览器登录；不要把 PAT 写入命令行。'
  gh auth login --hostname github.com --git-protocol https --web
  if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI 浏览器认证失败' }
  gh auth status
  if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI 认证状态复查失败' }
}
git switch main
if ($LASTEXITCODE -ne 0) { throw '切换 main 失败' }
git pull --ff-only
if ($LASTEXITCODE -ne 0) { throw '更新 main 失败' }
git switch -c codex/pr-agent-validation
if ($LASTEXITCODE -ne 0) { throw '创建验证分支失败；请检查同名分支是否已存在' }
$probePath = 'docs/pr-agent-validation-probe.md'
if (Test-Path -LiteralPath $probePath) { throw '验证探针文件已存在，停止以避免覆盖' }
Set-Content -LiteralPath $probePath -Encoding UTF8 -Value @(
  '# PR-Agent validation probe',
  '',
  '这是不含敏感数据的临时验证探针，验证完成后关闭 PR 并删除分支，永不合并。'
)
git add -- $probePath
if ($LASTEXITCODE -ne 0) { throw '暂存首个探针失败' }
git commit -m 'test: add temporary PR-Agent validation probe'
if ($LASTEXITCODE -ne 0) { throw '提交首个探针失败' }
git push -u origin codex/pr-agent-validation
if ($LASTEXITCODE -ne 0) { throw '推送验证分支失败' }
$prUrl = gh pr create --repo susz347/CodeSec-Agent --base main --head codex/pr-agent-validation --title 'test: validate PR-Agent deployment' --body 'Temporary non-sensitive probe. Do not merge; close and delete after Action and CLI verification.'
if ($LASTEXITCODE -ne 0 -or -not $prUrl.StartsWith('https://github.com/')) { throw '创建验证 PR 失败' }
Add-Content -LiteralPath $probePath -Encoding UTF8 -Value '第二次无敏感内容更新：仅用于验证 synchronize 只执行 /review。'
git add -- $probePath
if ($LASTEXITCODE -ne 0) { throw '暂存第二个探针失败' }
git commit -m 'test: update temporary PR-Agent validation probe'
if ($LASTEXITCODE -ne 0) { throw '提交第二个探针失败' }
git push
if ($LASTEXITCODE -ne 0) { throw '推送 synchronize 探针失败' }
$prUrl
```

在验证 PR 的 **Checks** 或仓库 **Actions** 页面确认首次运行和 `synchronize` 更新都成功；后者应只执行 `/review`，不能自动 describe 或 improve。检查 PR 评论和日志，确认没有输出 DeepSeek Key 或其他凭据。不要把启用 PR 当作验证 PR，也不要让验证 PR 承担长期功能变更。

## Phase 2：本地 PR-Agent CLI

### 1. 准备 Python 3.12 虚拟环境

PR-Agent 要求 Python 3.12 或更高版本。安装前先验证：

```powershell
py -3.12 --version
```

如果系统有 `py` 启动器：

```powershell
py -3.12 -m venv .venv
```

如果没有 `py`，使用本机 Python 3.12 可执行文件的绝对路径，例如：

```powershell
& 'C:\Path\To\Python312\python.exe' -m venv .venv
```

然后固定安装本地 CLI 并执行无凭据 smoke test：

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pr-agent==0.39.0
.\.venv\Scripts\python.exe -c "from importlib.metadata import version; assert version('pr-agent') == '0.39.0'; print(version('pr-agent'))"
.\.venv\Scripts\pr-agent.exe --help
```

`.venv/` 已由 `.gitignore` 排除，不应提交。

### 2. 创建最小权限 GitHub PAT

在 GitHub **Settings → Developer settings → Personal access tokens → Fine-grained tokens** 中创建短期 Token：

- Resource owner：拥有目标仓库的账号。
- Repository access：仅选择 `susz347/CodeSec-Agent`。
- Repository permissions：`Contents: Read-only`、`Pull requests: Read and write`；`Metadata: Read-only` 由 GitHub 自动授予。
- Expiration：建议 30 天或更短，用完后撤销。

不要为了省事创建 classic PAT、长期 Token 或全仓库 Token。若 GitHub 明确返回某项权限不足，只补充错误指出的必要权限。

### 3. 只在自己的终端注入凭据

在用户自己的 PowerShell 中运行以下命令。不要把真实值粘贴到聊天，也不要写入 `.env`、脚本、TOML 或其他文件：

```powershell
$deepSeekSecret = Read-Host 'DeepSeek API Key' -AsSecureString
$githubSecret = Read-Host 'GitHub Fine-grained PAT' -AsSecureString
$env:DEEPSEEK_API_KEY = [System.Net.NetworkCredential]::new('', $deepSeekSecret).Password
$env:GITHUB__USER_TOKEN = [System.Net.NetworkCredential]::new('', $githubSecret).Password
```

### 4. 执行并验证 review

对 Phase 1 创建的同一个短生命周期验证 PR 运行 CLI，并显式从可信默认分支读取配置：

```powershell
$prUrl = Read-Host '测试 PR 的完整 URL'
.\.venv\Scripts\pr-agent.exe --pr_url $prUrl --config-branch main review
```

成功标准：命令退出码为 `0`，终端没有认证或模型错误，目标 PR 出现新的 review 评论。确认评论基于本次 diff、有具体代码证据，并区分确认问题、可疑问题和可能误报。

如果在启用 PR 合并前必须做一次仅限维护者的本地配置预检，可显式使用 `--config-branch codex/pr-agent-phase1-2`。这会读取尚未合并的分支配置，只适用于已人工审查、无敏感探针内容的临时预检；不得用于 GitHub Action 或长期流程，也不能替代合并后的端到端验证。

### 5. 清理当前会话凭据

验证完成后立即运行：

```powershell
Remove-Item Env:DEEPSEEK_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:GITHUB__USER_TOKEN -ErrorAction SilentlyContinue
$deepSeekSecret = $null
$githubSecret = $null
```

关闭 PowerShell 也会清除进程环境变量，但仍应撤销不再使用的 PAT。

### 6. 删除验证垃圾

Phase 1 和 Phase 2 都验证完成后：

1. 关闭验证 PR，不合并临时探针，但暂时保留远端验证分支作为本地安全删除的参照。
2. 切回并快进更新 `main`，直接从 GitHub 远端读取明确分支的真实 SHA，并核对本地 SHA 完全相同。
3. 只有 SHA 相同才用安全的 `git branch -d` 删除本地分支，再用该 SHA 作为 lease 删除远端分支；远端若发生变化，删除必须失败。
4. 删除任何临时探针文件、日志和测试环境变量，并撤销不再需要的 PAT。

以下示例固定使用本文的验证分支名，不要改成通配符或批量删除命令：

```powershell
$ErrorActionPreference = 'Stop'
$validationPrNumber = Read-Host '验证 PR 编号'
gh pr close $validationPrNumber --repo susz347/CodeSec-Agent
if ($LASTEXITCODE -ne 0) { throw '关闭验证 PR 失败' }
git switch main
if ($LASTEXITCODE -ne 0) { throw '切换 main 失败' }
git pull --ff-only
if ($LASTEXITCODE -ne 0) { throw '更新 main 失败' }
$remoteRef = 'refs/heads/codex/pr-agent-validation'
$remoteLines = @(git ls-remote --heads origin $remoteRef)
if ($LASTEXITCODE -ne 0) { throw '读取远端验证分支失败' }
if ($remoteLines.Count -ne 1) { throw '远端验证分支结果不是唯一一条，停止清理' }
$remoteParts = $remoteLines[0] -split '\s+'
if ($remoteParts.Count -ne 2 -or $remoteParts[1] -ne $remoteRef -or $remoteParts[0] -notmatch '^[0-9a-fA-F]{40}$') { throw '远端验证分支结果格式无效，停止清理' }
$expectedSha = $remoteParts[0].ToLowerInvariant()
$localValidationSha = (git rev-parse codex/pr-agent-validation).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0) { throw '读取本地验证分支 SHA 失败' }
if ($localValidationSha -ne $expectedSha) { throw '本地与远端验证分支 SHA 不同，停止清理' }
git branch -d codex/pr-agent-validation
if ($LASTEXITCODE -ne 0) { throw '安全删除本地验证分支失败；禁止改用 -D' }
$leaseArg = "--force-with-lease=${remoteRef}:$expectedSha"
$deleteRefspec = ":$remoteRef"
git push $leaseArg origin $deleteRefspec
if ($LASTEXITCODE -ne 0) { throw '远端验证分支已变化或删除失败，停止清理' }
git branch --list
git status --short --branch
$remainingRemote = @(git ls-remote --heads origin $remoteRef)
if ($LASTEXITCODE -ne 0) { throw '无法复查远端验证分支' }
if ($remainingRemote.Count -ne 0) { throw '远端验证分支仍然存在' }
```

禁止使用 `git branch -D`。任一步骤失败都立即停止并报告，不要继续删除。切回 `main` 并安全删除本地验证分支后，未合并的探针文件会随分支自然消失，无需在 `main` 上手动删除。若使用 GitHub UI 关闭 PR，只关闭 PR，不要提前删除远端分支；随后从 `git switch main` 开始执行其余命令。

## Phase 3：本地 Semgrep 扫描

Phase 3 首版只运行 Semgrep。它使用固定的 `1.163.0` 版本和 `p/security-audit` 规则集，将原始输出与统一 finding 文档写入被 Git 忽略的 `artifacts/`。规则集由 Semgrep Registry 提供，因此首次真实扫描需要网络访问。扫描发现不会阻断合并，也不会调用 DeepSeek 或向 PR 写评论。

在仓库根目录执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m scanner.run_semgrep --target . --artifacts artifacts
Get-Content -LiteralPath 'artifacts\findings.json' -Raw | ConvertFrom-Json | ConvertTo-Json -Depth 8
```

如尚未创建 `.venv`，先用可用 Python 3.12+ 创建它。Bandit 使用固定的 `1.9.4` 版本；npm audit 要求目标含 `package-lock.json`，并以 `--package-lock-only --ignore-scripts` 运行，不安装或执行依赖脚本。不要提交 `artifacts/`；其中的产物仅供本地验证或后续受控的自动化流程使用。

## Phase 4：本地五格式报告

报告 CLI 接收一个或多个 Phase 3 生成的 schema 1.0 finding 文档，统一校验、合并和排序。默认仍只生成 `security-report.json` 与 `security-report.md`；`--format all` 额外生成 `security-report.xlsx`、`security-report.docx` 和 `security-report.pdf`。

首次使用多格式报告时安装固定依赖。npm 命令禁用依赖脚本；安装完成后，报告生成过程不访问网络：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm install --ignore-scripts
```

以下命令合并 Semgrep、Bandit 和 npm audit 的本地结果并生成全部五种格式：

```powershell
.\.venv\Scripts\python.exe -m reporting.cli `
  --input artifacts\findings.json `
  --input artifacts\bandit-findings.json `
  --input artifacts\npm-audit-findings.json `
  --output-dir artifacts `
  --format all
```

`--format` 可重复指定 `json`、`markdown`、`xlsx`、`docx` 或 `pdf`；不指定时保持 JSON/Markdown 兼容行为。所有选中格式只会作为一个报告组更新；输入无效、渲染失败或提交任一文件失败时，命令返回非零退出码、清理临时文件并恢复原有报告组。零发现是成功结果。

DOCX 生成需要 Node.js；PDF 默认查找 Windows Microsoft YaHei、Linux Noto Sans CJK 或 DejaVu Sans，也可通过进程级 `CODESEC_REPORT_FONT` 指定 TTF/TTC 字体。当前切片不调用 DeepSeek、不访问 GitHub。`artifacts/` 已被 Git 忽略，不要将真实扫描结果或报告提交到仓库。

### 确定性分析 Agent、增强报告与 PR 摘要

分析 Agent 接收一个或多个 Phase 3 生成的 schema 1.0 finding 文档，按严重度与规则知识对每条 finding 做确定性分类（`confirmed` / `suspicious` / `possible_false_positive`），并组装成因、影响、修复建议与 CWE/OWASP 参考。它只读归一化 finding 的 `code` 与 `message`，不读源文件、不调用 DeepSeek、不访问 GitHub：

```powershell
.\.venv\Scripts\python.exe -m agent.cli `
  --input artifacts\findings.json `
  --input artifacts\bandit-findings.json `
  --input artifacts\npm-audit-findings.json `
  --output-dir artifacts
```

命令原子写出 `artifacts\analysis.json` 与 `artifacts\analysis.md`。传给 `reporting.cli` 的 `--analysis` 可选参数后，JSON 与 Markdown 报告会升级为增强版：每条 finding 附带分类、成因、影响、修复建议与参考。不传 `--analysis` 时行为与前述五格式报告完全一致：

```powershell
.\.venv\Scripts\python.exe -m reporting.cli `
  --input artifacts\findings.json `
  --input artifacts\bandit-findings.json `
  --input artifacts\npm-audit-findings.json `
  --analysis artifacts\analysis.json `
  --output-dir artifacts `
  --format markdown
```

`reporting.summary` 从增强 JSON 报告生成仅含 finding 总数、各级严重度计数、分类计数、rule_id 列表、path 列表与产物链接的紧凑摘要，绝不包含源码或凭据；`error>0` 时追加「建议人工复核」提示，但只是提示、不阻断：

```powershell
.\.venv\Scripts\python.exe -m reporting.summary `
  --report artifacts\security-report.json `
  --artifacts-url "https://github.com/<owner>/<repo>/actions/runs/<run_id>" `
  --output pr-summary.md
```

上述「扫描 → 分析 → 增强报告 → 产物上传 → PR 摘要」流程已固化为 [`.github/workflows/security-scan.yml`](../.github/workflows/security-scan.yml)，与 `pr-agent.yml` 一致跳过 Fork 与 Bot、仅用 `contents: read` 加 `pull-requests: write`，且扫描发现本身永不 fail 作业。合并阻断策略、真实 DeepSeek 调用与分支推送留待单独授权。

## 故障排查

| 现象 | 处理方式 |
| --- | --- |
| DeepSeek 401 | Key 无效、已撤销或未正确注入。重新配置 Secret/环境变量，不要打印 Key。 |
| DeepSeek 402 | 检查 DeepSeek 余额和计费状态。 |
| DeepSeek 429 | 等待限流窗口后重试，避免连续更新 PR。 |
| model not found | 确认 `.pr_agent.toml` 使用 `deepseek/deepseek-v4-flash`，不要改成旧模型名。 |
| GitHub 403 | 确认仓库范围正确，并检查 `Contents: Read-only` 与 `Pull requests: Read and write`。按明确错误补权限，不授予全量权限。 |
| Fork PR 或 Bot 没有运行 | 这是当前安全边界，不要改用 `pull_request_target` 绕过。请用同仓库、非 Bot 分支验证。 |
| `py -3.12` 不可用 | 安装 Python 3.12，或用 Python 3.12 `python.exe` 的绝对路径创建 `.venv`。 |
| 受限环境提示 Azure DevOps 缓存目录不可写 | 仅在 Codex 等受限环境中，将进程级缓存指向已经存在且可写的目录后重试：`$env:AZURE_DEVOPS_CACHE_DIR = 'C:\tmp'`。不要新建缓存子目录，也不要把该变量写入脚本。普通用户无需设置。 |
| LiteLLM 无法联网更新模型/价格数据的 warning | 若 review 仍继续，这是使用随包数据回退的非致命 warning；记录即可。若随后 API 调用失败，再检查 DNS、代理和 DeepSeek 连通性。 |
| 提示未找到 `.secrets.toml` | 本项目刻意通过进程环境变量注入凭据，这是预期 warning；不要为消除提示而创建含密钥的文件。 |
| CLI 找不到配置 | 从仓库根目录运行，并确认默认分支 `main` 包含 `.pr_agent.toml`；正式验证使用 `--config-branch main`。 |

## 完成标准

- GitHub Actions 能在同仓库测试 PR 上发布自动 review，并在更新提交后只重新 review。
- 本地 `pr-agent==0.39.0` 能对同一个短生命周期验证 PR 发布 review。
- 启用 PR 已经用户明确批准并合并；首个启用 PR 未被误当成端到端验证。
- Action 与正式本地验证都从默认分支 `main` 读取已审核的 `.pr_agent.toml` 和 DeepSeek 模型。
- Workflow、TOML、Git 历史和日志中均无 API Key 或 PAT。
- 验证 PR 已关闭且未合并，远端/本地验证分支、临时探针、环境变量和不再需要的 PAT 均已清理。
