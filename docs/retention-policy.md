# 产物保留与归档策略

本文是 [故障 Runbook](runbook.md) 的收尾步骤，定义扫描产物 30 天保留期到期后的归档/删除责任，目标是降低密钥、报告与日志的操作风险，并让处置可落到具体责任人。

## 1. 范围与分类

| 类别 | 产物 | 敏感级别 | 来源 |
| --- | --- | --- | --- |
| 原始扫描结果 | `artifacts/bandit-result.json`、`artifacts/semgrep-result.json`、`artifacts/npm-audit-result.json` | 敏感（含目标源码片段/路径） | 本地扫描生成，**CI 不上传** |
| 归一化 finding | `artifacts/findings.json`、`bandit-findings.json`、`npm-audit-findings.json` | 中（含 `code` 与 `message`） | 本地 + CI 上传 |
| 分析结果 | `artifacts/analysis.json` | 敏感（`evidence` 含源码行 + sha256） | 本地 + CI 上传 |
| 报告 | `security-report.{json,md,xlsx,docx,pdf}` | 敏感（增强版含 evidence 摘要） | 本地 + CI 上传 |
| 产物清单 | `manifest.json` | 低（文件名 + 字节数 + sha256） | 本地 + CI 上传 |
| PR diff | `artifacts/pr.diff` | 敏感（变更源码） | CI 本地生成，**不上传** |

## 2. 保留期

- CI 上传产物：`.github/workflows/security-scan.yml` 的 `Upload reports` 步骤已配置 **`retention-days: 30`**，到期由 GitHub 自动删除（实际 workflow 配置，非口头策略）。
- 本地 `artifacts/`：默认不长期保留，演示/验证后即删。

## 3. 责任与动作

| 动作 | 责任人 | 时机 | 操作 |
| --- | --- | --- | --- |
| 常规删除 | 触发 CI 的维护者 | 不需要留存时 | `gh run delete <run-id> --repo susz347/CodeSec-Agent`，或等待 30 天自动过期 |
| 本地清理 | 任何在本地跑扫描的人 | 演示/验证结束后 | 删除 `artifacts/`，不提交 |
| 归档留存 | 需要作为验收/审计证据的维护者 | 30 天到期前 | 先下载再归档到受控存储（见 §4） |
| 密钥泄露应急 | 发现疑似泄漏的任何人 | 立即 | 先轮换密钥（[Runbook §5.1](runbook.md#51-deepseek-key-轮换)），再删除涉事产物，最后记录 |

## 4. 归档流程

需要留存证据时（如 P0 验收、审计），在 30 天到期前：

```powershell
gh run download <run-id> --repo susz347/CodeSec-Agent --name security-scan-reports
```

归档原则：

- 归档到受控、访问受限的位置，不放入公开仓库或聊天。
- 只归档「结论 + 摘要」，避免长期留存含源码 evidence 的 `analysis.json` 与增强报告；确需留存时记录用途与到期日。
- 归档同时记录 `run-id`、归档日期、责任人，便于追溯。

## 5. 删除流程

1. 确认产物无留存需要（或已按 §4 归档）。
2. CI 产物：`gh run delete <run-id> --repo susz347/CodeSec-Agent`；或确认 30 天自动过期。
3. 本地产物：删除 `artifacts/` 目录。
4. 复核 `manifest.json` 与归档记录一致，关闭处置闭环。

## 6. 异常处理

- 产物被篡改或 `manifest.json` 校验不通过：丢弃并重跑（见 [Runbook §3.4](runbook.md#34-artifact-异常)），不得沿用可疑产物。
- 归档/删除失败：记录原因，不静默跳过；必要时提升给仓库维护者处理。
