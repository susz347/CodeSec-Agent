# Baseline 与人工处置数据设计（#5）

> 状态：已批准实现。第一版使用仓库内版本化 `.codesec/triage.json`，不引入数据库、UI 或真实模型调用。

## 目标

为「风险评分」与「误报校准」建立可追溯的真值数据：让每条 finding 从「机器判定」走向「经人工处置后可用于校准」的记录。核心是回答两个问题：

1. 这条 finding 最终**是不是问题**（真阳性 / 误报）？
2. 机器的判定（`label`、`diff_status`、严重度）与人工结论**差多远**？

## 关键约束

- **不先于数据实现**：存储与统计逻辑必须等真实 CI 产出 `changed`/`evidence` 之后再做。本设计只冻结契约，避免后续实现反复改数据结构。
- **证据不可变**：处置记录引用扫描与分析的不可变快照（`finding_id` + 快照哈希），不复制 `code`/`evidence` 正文。
- **最小权限**：处置数据属人工反馈，不含源码片段与凭据，可与报告产物分离存储。

## 数据契约（schema 1.0）

```json
{
  "schema_version": "1.0",
  "triage_id": "<uuid>",
  "finding_id": "<归一化 finding 的 id>",
  "snapshot": {
    "analysis_sha256": "<该 finding 对应 analysis item 的稳定哈希>",
    "diff_status": "changed | unchanged | unknown",
    "machine_label": "confirmed | suspicious | possible_false_positive"
  },
  "human_verdict": {
    "resolution": "true_positive | false_positive | accepted_risk | needs_fix",
    "severity_override": "error | warning | info | unknown | null",
    "note": "<人工备注，不含源码>",
    "reviewer": "<处置者标识>",
    "reviewed_at": "<ISO-8601>"
  }
}
```

顶层文件同时保存默认分支基线与处置记录：

```json
{
  "schema_version": "1.0",
  "baseline": {"generated_at": "<ISO-8601>", "findings": []},
  "dispositions": []
}
```

基线 finding 仅保存稳定 fingerprint、工具、规则和路径；不保存源码、代码上下文或完整扫描报告。fingerprint 基于工具、规则、相对路径与规范化代码（缺代码时使用规范化消息），故普通行号移动不会把历史 finding 误判为新增。

### 字段说明

- `triage_id`：处置记录主键，独立于 finding，允许同一 finding 多次处置（版本演进）。
- `snapshot.analysis_sha256`：把「该 finding 的 analysis item 关键字段（label/diff_status/evidence 摘要/rule_id/severity）」做稳定序列化后哈希，保证处置记录指向的是当时那一版分析，而非后来被覆盖的版本。
- `human_verdict.resolution`：人工最终结论，是校准的标签源。`needs_fix` 表示真问题且需要修复；`accepted_risk` 表示确认真问题但接受风险。
- `severity_override`：允许人工修正严重度，覆盖扫描器/Agent 的初始值。

## 校准流程

```
真实 CI 扫描 → findings + analysis（含 changed/evidence）
  → 人工按风险排序（confirmed+changed 优先）逐条处置
  → 写入处置记录（上述 schema）
  → 按 snapshot.analysis_sha256 对齐 machine_label 与 human_verdict
  → 计算校准指标：precision/recall 按 label、diff_status、rule_id 分层
```

CLI 提供三类本地操作：写入/更新基线、写入人工处置、输出按工具/规则/机器标签分层的处置统计。统计只读，不反向修改分析逻辑——先观察再调整规则（如 `HIGH_CONFIDENCE` 集、测试路径降级启发式）。

## 与风险排序的关系

`reporting/risk.py` 的排序使用确定性 label；待处置数据积累后，**风险评分**才可能引入人工校准的权重。在评分落地前，排序保持纯确定性、无统计参数。

## 边界（本次不做）

- 处置 UI 或采集工具。
- 风险评分数值模型。
