# PR-Agent Phase 1/2 部署设计

## 1. 目标

本轮只完成 `docs/deployment-steps.md` 中的前两个阶段：

1. 在 GitHub Actions 中自动运行 PR-Agent，对当前仓库的 Pull Request 发表评论。
2. 在 Windows 本机通过 Python 虚拟环境运行 PR-Agent CLI，对指定 Pull Request 执行审查。

两个入口统一使用 DeepSeek API 和同一份仓库级 PR-Agent 配置。本轮不接入 Semgrep、Bandit、npm audit，不实现扫描结果归一化、安全分析 Agent 或 Markdown 报告生成器。

## 2. 已确认的约束

- 目标仓库：`susz347/CodeSec-Agent`。
- 模型提供商：DeepSeek。
- 首选模型：`deepseek/deepseek-v4-flash`。
- 用户已有 DeepSeek API Key，但不会将密钥发送到对话或写入仓库。
- 用户尚无 GitHub Personal Access Token；Phase 2 包含最小权限 Token 的创建说明。
- PR-Agent 固定使用 `0.41.0`，避免部署结果随上游 `main` 变化。
- 首版仅执行 review，不自动执行 describe 或 improve。
- 首版只处理同一仓库分支创建的 PR，不支持来自 Fork 的 PR。

## 3. 方案选择

采用“共享配置 + 两种运行入口”：

- `.pr_agent.toml` 保存非敏感、可共享的模型和审查行为配置。
- `.github/workflows/pr-agent.yml` 负责 GitHub Actions 触发、权限和 Secret 注入。
- 本地 CLI 通过当前 PowerShell 会话中的环境变量注入 DeepSeek Key 和 GitHub Token。

该方案避免在 GitHub Actions 和本地命令中重复维护模型及审查规则，同时不把凭据写入配置文件。

未采用以下方案：

- 所有配置都写在 workflow：文件较少，但本地 CLI 与 CI 容易出现配置漂移。
- 全部使用 Docker：隔离更强，但对当前以 Windows 和 Python CLI 为主的初学部署增加了调试成本。

## 4. Phase 1：GitHub Actions

### 4.1 文件

创建：

```text
.github/workflows/pr-agent.yml
.pr_agent.toml
```

修改：

```text
.gitignore
docs/deployment-steps.md
```

如果仓库还没有 `.gitignore`，则创建该文件。

### 4.2 触发方式

Workflow 监听：

```yaml
pull_request:
  types: [opened, reopened, ready_for_review, synchronize]
```

首版不监听 `issue_comment`，防止公共仓库中的任意评论反复消耗模型额度；不使用 `pull_request_target`，避免让不受信任的 Fork PR 获得仓库 Secret 上下文。

### 4.3 权限

Workflow 使用最小可行权限：

```yaml
permissions:
  contents: read
  issues: write
  pull-requests: write
```

不授予 `contents: write` 或 `checks: write`，因为本轮不修改仓库内容，也不把结果发布为 GitHub Check。

### 4.4 Action 固定版本

使用 PR-Agent `v0.41.0` 对应的完整提交 SHA：

```text
the-pr-agent/pr-agent@570f67ed5fc8db5be74c18df070bc20079b64b0d
```

固定完整 SHA 可避免可变分支或标签在未审查的情况下改变运行代码。

### 4.5 模型与 Secret

GitHub 仓库需要人工创建以下 Repository Secret：

```text
DEEPSEEK_API_KEY
```

Workflow 注入：

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
```

`GITHUB_TOKEN` 由 GitHub Actions 自动提供，不创建个人 Token，也不持久化到仓库。

### 4.6 共享配置

`.pr_agent.toml` 负责：

- 将模型固定为 `deepseek/deepseek-v4-flash`。
- 关闭不在本轮范围内的自动 describe 和 improve。
- 为 review 增加安全审查指令。
- 要求输出区分确认问题、可疑问题和可能误报。

配置文件不得包含 API Key、GitHub Token 或其他凭据。

## 5. Phase 2：本地 CLI

### 5.1 Python 环境

本机使用 Python 3.12 创建项目内虚拟环境：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pr-agent==0.41.0
```

`.venv/` 必须加入 `.gitignore`。

### 5.2 GitHub Token

本地 CLI 需要 GitHub Fine-grained Personal Access Token，用于读取 PR 并发布评论。Token 配置为：

- Repository access：仅 `susz347/CodeSec-Agent`。
- Contents：Read。
- Pull requests：Read and write。
- Issues：Read and write。
- 建议过期时间：30 天。

如果 PR-Agent 在实际调用中返回权限不足，只增加错误明确指出的必要权限，不改用覆盖全部仓库的长期 Token。

### 5.3 本地环境变量

用户在当前 PowerShell 会话中设置：

```powershell
$env:DEEPSEEK_API_KEY="<DeepSeek API Key>"
$env:GITHUB__USER_TOKEN="<GitHub Fine-grained PAT>"
```

密钥不得写入 PowerShell 脚本、`.pr_agent.toml`、`.env` 或 Git 历史。

### 5.4 CLI 调用

在仓库根目录运行：

```powershell
.\.venv\Scripts\pr-agent.exe `
  --pr_url https://github.com/susz347/CodeSec-Agent/pull/<PR编号> `
  review
```

CLI 与 GitHub Actions 都以目标仓库中的 `.pr_agent.toml` 为非敏感配置来源。

运行结束后从当前会话清除凭据：

```powershell
Remove-Item Env:DEEPSEEK_API_KEY
Remove-Item Env:GITHUB__USER_TOKEN
```

## 6. 数据流

### 6.1 GitHub Actions

```text
仓库内分支创建或更新 PR
→ GitHub 触发 pull_request workflow
→ GitHub 注入 GITHUB_TOKEN 和 DEEPSEEK_API_KEY
→ PR-Agent 读取 PR diff 与 .pr_agent.toml
→ PR-Agent 调用 DeepSeek
→ PR-Agent 把审查评论写回 PR
```

### 6.2 本地 CLI

```text
用户在 PowerShell 临时设置两个 Token
→ pr-agent CLI 读取 PR URL
→ 使用 GitHub PAT 获取 PR 上下文
→ 读取目标仓库的 .pr_agent.toml
→ 调用 DeepSeek
→ 使用 GitHub PAT 把评论写回 PR
→ 用户清除当前会话环境变量
```

## 7. 错误处理

| 症状 | 判定与处理 |
| --- | --- |
| DeepSeek 401 | Key 无效、已撤销或未正确注入；重新检查 Secret/环境变量，不输出 Key |
| DeepSeek 402 | 账户余额或计费状态不可用；在 DeepSeek 控制台处理 |
| DeepSeek 429 | 达到请求速率限制；等待后重试，避免重复触发 PR |
| model not found | 检查模型是否为 `deepseek/deepseek-v4-flash` |
| GitHub 403 | 检查 workflow 权限或 Fine-grained PAT 的仓库与权限范围 |
| Fork PR 无法读取 Secret | 属于首版明确不支持的场景，不切换到 `pull_request_target` 绕过 |
| CLI 找不到 Python 3.12 | 安装 Python 3.12 并确认 `py -3.12 --version` 可用 |
| CLI 找不到配置 | 确认命令从仓库根目录执行且 `.pr_agent.toml` 已提交到目标分支 |

错误日志允许包含状态码、请求 ID 和错误类型，但不得打印完整 API Key 或 GitHub Token。

## 8. 验证策略

本轮只有配置、部署文档和外部工具安装，不新增业务函数，因此不创建业务单元测试。验证分三层进行：

1. 静态验证
   - 检查 YAML 和 TOML 语法。
   - 检查 Action 引用是否固定到完整 SHA。
   - 搜索仓库，确认没有疑似 DeepSeek Key 或 GitHub Token 被写入文件。
2. 本地 smoke test
   - `py -3.12 --version`。
   - `pr-agent --help`。
   - 使用临时环境变量对测试 PR 执行一次 `review`。
3. GitHub 端到端测试
   - 先把 workflow 和配置合并到默认分支。
   - 从同一仓库创建测试分支和测试 PR。
   - 确认 GitHub Actions 成功且 PR 出现审查评论。

涉及真实 API 调用的验证可能产生少量 DeepSeek 费用。执行前只确认密钥已由用户安全设置，不读取或回显密钥值。

## 9. 验收标准

Phase 1 完成条件：

- `.github/workflows/pr-agent.yml` 和 `.pr_agent.toml` 已在默认分支。
- GitHub Repository Secret `DEEPSEEK_API_KEY` 已配置。
- 同仓库测试 PR 能触发 Action。
- Action 成功调用 DeepSeek 并发布审查评论。
- Workflow 日志没有泄露凭据。

Phase 2 完成条件：

- Python 3.12 虚拟环境创建成功。
- `pr-agent==0.41.0` 安装成功。
- Fine-grained PAT 仅授权当前仓库和必要权限。
- 本地 CLI 能对测试 PR 执行 `review` 并发布评论。
- 测试完成后当前 PowerShell 会话中的凭据已清除。

## 10. 非目标

本轮不包含：

- Semgrep、Bandit 或 npm audit。
- 扫描器 JSON 解析和 finding 归一化。
- 自定义安全分析 Agent。
- Markdown、Word 或 PDF 报告生成。
- RAG、OWASP/CWE 知识库。
- 自动修复、合并阻断、Web UI。
- Fork PR、GitHub App 或自托管 runner。

这些能力在 Phase 1/2 验收后按 `docs/roadmap.md` 继续推进。

## 11. 参考资料

- PR-Agent GitHub 安装：https://docs.pr-agent.ai/installation/github/
- PR-Agent 本地安装：https://docs.pr-agent.ai/installation/locally/
- PR-Agent 上游仓库：https://github.com/The-PR-Agent/pr-agent
- DeepSeek API：https://api-docs.deepseek.com/zh-cn/
- LiteLLM DeepSeek Provider：https://docs.litellm.ai/docs/providers/deepseek
- GitHub Actions 安全加固：https://docs.github.com/en/actions/reference/security/secure-use
