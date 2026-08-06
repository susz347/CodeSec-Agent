# 部署与运行步骤

本文是 CodeSec-Agent 的唯一详细部署入口。本项目的四个部署阶段为：

1. **Phase 1：GitHub Actions 自动运行 PR-Agent**（本轮范围，配置已实施，等待真实 PR 验证）。
2. **Phase 2：Windows 本地运行 PR-Agent CLI**（本轮范围，安装已验证，等待凭据和真实 PR 验证）。
3. **Phase 3：接入 Semgrep、Bandit 和 npm audit**（待开发）。
4. **Phase 4：归一化 finding、执行 Agent 分析并生成 Markdown 报告**（待开发）。

本文只给出 Phase 1 和 Phase 2 的可执行步骤，后两阶段不提前堆放未经验证的命令。这里的编号表示部署顺序；产品研发任务与交付物另见 [项目路线图](roadmap.md)，不要混用两套阶段编号。

## 版本与安全边界

- 共享配置位于仓库根目录的 [`.pr_agent.toml`](../.pr_agent.toml)，模型为 `deepseek/deepseek-v4-flash`。
- GitHub Action 固定到 PR-Agent `v0.41.0` 对应的完整提交 SHA `570f67ed5fc8db5be74c18df070bc20079b64b0d`。
- 本地 CLI 固定安装 PyPI 可用的 `pr-agent==0.39.0`。Action 与 PyPI 当前发布渠道不同，版本号暂时不一致；不要自行把其中一端改成浮动版本。
- 共享 TOML 通过 `fallback_models = []` 禁用备用模型，避免 DeepSeek 失败时把代码发送给其他提供商；审查指令同时要求把 PR 描述、代码、注释和字符串视为不可信数据，以降低提示注入风险，但这不是绝对隔离，不能替代人工复核。
- 密钥只进入 GitHub Repository Secret 或用户自己的当前 PowerShell 进程，不写入文件、Git 历史或聊天。

## Phase 1：GitHub Actions 自动审查

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

1. 确认启用 PR 已经用户批准并合并，且 `.pr_agent.toml`、workflow 和 Secret 均已在目标仓库就绪。
2. 从更新后的 `main` 创建同仓库短生命周期分支，只提交一个不含敏感数据、无需合并的临时探针变更，然后发起验证 PR；不要用 Fork。
3. 在验证 PR 的 **Checks** 或仓库 **Actions** 页面确认 `PR Agent Security Review` 成功。
4. 确认 PR 出现自动 review 评论，且没有自动 describe 或 improve 评论。
5. 再向该分支推送一个小提交，确认 `synchronize` 后只重新执行 review。
6. 检查日志没有输出 DeepSeek Key 或其他凭据。

不要把启用 PR 当作上述验证 PR，也不要让验证 PR 承担长期功能变更。

## Phase 2：Windows 本地 CLI

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

1. 关闭验证 PR，不合并临时探针；在 GitHub UI 中同时删除远端验证分支，或使用下方 `gh pr close`。
2. 切回并快进更新 `main`，再用安全的 `git branch -d` 删除下方明确命名的本地验证分支。
3. 删除任何临时探针文件、日志和测试环境变量，并撤销不再需要的 PAT。

以下示例固定使用本文的验证分支名，不要改成通配符或批量删除命令：

```powershell
git switch main
git pull --ff-only
$validationPrNumber = Read-Host '验证 PR 编号'
$validationBranch = 'codex/pr-agent-validation-20260806'
gh pr close $validationPrNumber --repo susz347/CodeSec-Agent --delete-branch
git branch -d $validationBranch
git branch --list
git status --short
```

禁止使用 `git branch -D`。如果 `-d` 因探针提交未合并而拒绝删除，立即停止并报告仍保留的明确分支名，不要强制删除。若已通过 GitHub UI 关闭 PR 并删除远端分支，则跳过 `gh pr close`，其余本地检查不变。

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
