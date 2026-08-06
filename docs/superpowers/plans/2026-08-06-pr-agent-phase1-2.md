# PR-Agent Phase 1/2 实施与验收记录

本文只记录任务状态、依赖和验收点，不维护第二份部署命令。所有可执行步骤统一见 [部署与运行步骤](../../deployment-steps.md)；实际配置以仓库根目录的 [`.pr_agent.toml`](../../../.pr_agent.toml) 和 [PR-Agent workflow](../../../.github/workflows/pr-agent.yml) 为准。

## 固定决策

- Phase 1：GitHub Actions 自动运行 PR-Agent。
- Phase 2：Windows 本地运行 PR-Agent CLI。
- GitHub Action 固定到 v0.41.0 的完整提交 SHA；本地 PyPI 包固定为 `pr-agent==0.39.0`。
- 两条路径使用 DeepSeek V4 Flash，并从默认分支 `main` 读取已审核的共享配置。
- Workflow 只处理同仓库、非 Bot PR，权限仅为 Contents read 与 Pull requests write；`synchronize` 只运行 review。
- 提示指令只能降低提示注入风险，不能提供绝对隔离。
- PR 内容会发送给 DeepSeek；首次验证不得包含密钥、客户数据、生产数据、真实漏洞或利用步骤。
- 启用 PR 需用户明确批准后才合并；它不承担端到端验证。
- 端到端验证使用从更新后 `main` 创建的短生命周期 PR，探针永不合并并在验证后清理。

## 任务记录

### Task 1：隔离实施分支

- 状态：已完成。
- 依赖：批准的设计与实施范围。
- 验收：独立 worktree 使用 `codex/pr-agent-phase1-2`，初始状态干净。

### Task 2：保护本地凭据和生成状态

- 状态：已完成。
- 依赖：Task 1。
- 验收：虚拟环境、进程凭据文件和根目录日志被忽略；环境模板和嵌套测试日志仍可跟踪。

### Task 3：安装本地 CLI

- 状态：已完成。
- 依赖：Python 3.12 或更高版本。
- 验收：本地包版本为 0.39.0，帮助命令成功，安装未污染 Git 状态。

### Task 4：共享非敏感配置

- 状态：已完成。
- 依赖：Task 3。
- 验收：共享配置固定模型、禁用备用模型、加入安全审查与不可信输入指令，且不含凭据。

### Task 5：最小权限 GitHub workflow

- 状态：已完成。
- 依赖：Task 4。
- 验收：触发器、同仓库/Fork guard、Bot guard、15 分钟超时、最小权限及 synchronize review 行为与实际 workflow 一致。

### Task 6：单一权威部署文档

- 状态：已完成。
- 依赖：Tasks 2–5 的最终实现。
- 验收：README 仅保留入口摘要；部署、验证、清理和故障排查只在权威部署指南维护；公开链接有效。

### Task 7：本地静态验证

- 状态：已完成。
- 依赖：Tasks 2–6。
- 验收：TOML/YAML 可解析，版本和安全断言通过，无凭据样式值，工作树在提交后干净。

### Task 8：发布并合并启用 PR

- 状态：等待发布、评审和用户批准。
- 依赖：Tasks 1–7。
- 验收：完整分支 diff 通过规格与质量审核；用户明确批准；workflow 与共享配置进入 `main`。启用 PR 不作为端到端验证证据。

### Task 9：配置凭据

- 状态：等待 Task 8 合并。
- 依赖：已向用户说明 DeepSeek 数据外发边界。
- 验收：Repository Secret 已设置；短期 Fine-grained PAT 仅限目标仓库、Contents read 与 Pull requests read/write；未读取或回显值。

### Task 10：创建短生命周期验证 PR

- 状态：等待 Tasks 8–9。
- 依赖：更新后的 `main`、按官方浏览器流程完成认证的 GitHub CLI、仓库根目录；不得把 PAT 写入命令行。
- 验收：固定验证分支和明确探针文件按权威指南创建；首次提交触发 opened，第二次提交触发 synchronize；PR 不含敏感或攻击性内容并标记为永不合并。

### Task 11：验证 Action 与本地 CLI

- 状态：等待 Task 10。
- 依赖：同一个验证 PR、用户终端中的临时凭据。
- 验收：Action 首次审查成功，synchronize 只 review；本地 CLI 使用 `main` 配置成功发布第二次审查；日志不含凭据；进程环境变量已清除。

### Task 12：关闭验证 PR 并清理

- 状态：等待 Task 11。
- 依赖：两条验证路径均有成功证据。
- 验收：验证 PR 未合并；从真实远端引用读取唯一 SHA 并与本地核对一致；本地安全删除后使用 expected-SHA lease 删除远端分支，远端变化时必须失败停止；禁止本地强制删除；切回 `main` 后探针自然消失；日志、环境变量和不再需要的 PAT 已清理；最终状态已报告。

## 完成条件

只有 Tasks 1–12 的验收证据齐全，才能声明 Phase 1 和 Phase 2 完成。合并启用 PR、调用 DeepSeek、创建/关闭验证 PR、删除远端分支和撤销 PAT 都必须遵守各自的用户批准与安全边界。
