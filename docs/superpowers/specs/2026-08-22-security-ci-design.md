# 安全扫描 CI 与 PR 摘要设计

## 目标

新增独立安全扫描 workflow，跑通「扫描 → 分析 → 多格式报告 → 产物上传 → PR 摘要」，默认只提示、不阻断合并。

## 安全边界

- 权限：`contents: read` + `pull-requests: write`（仅用于发布摘要评论）。
- 不使用 `pull_request_target`；与 `pr-agent.yml` 一致跳过 Fork 与 Bot。
- 摘要只含 finding 总数、各级严重度计数、分类计数、rule_id 列表、path 列表、产物链接；不含源码或凭据。

## 流程

```
checkout -> setup Python 3.12 / Node 20 -> 安装依赖
  -> run_semgrep -> run_bandit -> run_npm_audit（各自写 artifacts/）
  -> agent.cli（确定性分析，写 analysis.json/.md）
  -> reporting.cli --analysis --format all（写五种报告）
  -> upload-artifact（原始/归一化/分析/报告产物）
  -> reporting.summary（读增强 JSON，写 pr-summary.md）
  -> gh pr comment（发布摘要）
```

## 风险阈值与阻断策略

- 阈值内联在 `reporting.summary`：`error>0` 时摘要追加「建议人工复核」警告。
- **只提示，不阻断**：扫描发现本身永不 fail 作业；仅基础设施错误（扫描器未安装、JSON 无法解析）fail。
- 合并阻断策略需要真实误报数据与用户单独授权，本次不实现。

## 验收

- YAML 静态检查（`git diff --check`）、最小权限、Bot/Fork guard。
- `reporting.summary` 单测：含计数/分类/rule/path、不含源码、error>0 触发警告。
- 同仓库非 Bot PR 成功运行、产物可下载、摘要无敏感内容。
