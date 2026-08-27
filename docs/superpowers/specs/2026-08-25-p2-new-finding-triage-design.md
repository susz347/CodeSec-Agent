# P2 新发现人工 Triage 最小修补设计

## 目标

让真实 PR 中不在 baseline 的 `new` finding 能写入现有 `.codesec/triage.json` 的 `dispositions`，从而完成“扫描 → 人工 triage → 持久化 → 规则级统计”的试运行闭环。

## 现状与缺口

`agent.triage_cli disposition` 目前只接收 fingerprint。`agent.triage.add_disposition` 会在 baseline 中查找该 fingerprint，找不到就报 `Unknown baseline fingerprint`。因此真实 PR 的新增 finding 无法持久化处置；而 P2 规范要求这些 finding 必须进入 triage store。

现有 workflow、扫描器、分析、PR 摘要、基线比较和 `statistics()` 已分别承担自己的职责；本修补不改变它们。

## 设计

### CLI 入口

保留既有 `--fingerprint` 用法，并增加一组互斥参数：

```text
--input <normalized-findings.json> --finding-id <id>
```

当用 `--finding-id` 处置时，CLI 从已有 schema 1.0 finding 文档读取指定 finding，计算稳定 fingerprint，并将该 finding 的 `tool` 和 `rule_id` 传给 triage 层。找不到或重复的 finding ID 是干净错误，不写文件。

### 存储语义

`add_disposition` 接受一个可选的 finding 记录：

- fingerprint 属于 baseline 时，沿用当前行为；
- fingerprint 不属于 baseline 且提供 finding 时，允许写入 disposition；
- fingerprint 不属于 baseline 且未提供 finding 时，继续拒绝，避免凭手输 fingerprint 产生无法归类的记录。

写入内容保持既有 disposition 字段：fingerprint、resolution、reviewer、machine_label、note、reviewed_at、tool、rule_id。不会把 finding 的源码、path、message、evidence、PR URL 或扫描报告保存到 store。相同 fingerprint 仍采用“最后一次人工结论覆盖前一次”的现有去重语义，因此同一 finding 不会被重复累计。

### 日志模板

`docs/trial-phase-2-log.md` 的 PR 记录增加规则 ID 汇总（无路径/源码）；漏报种子表增加 PR 或受控索引、风险依据、未命中原因及未来 detector/rule 方向。它仍是去标识化运营日志，不新增数据模型或自动上传机制。

## 非目标

- 不改变 baseline 格式、baseline 状态计算或 `.codesec/triage.json` schema version。
- 不更改 scanner、workflow、DeepSeek、报告、RAG、风险评分、UI、规则集、merge gate 或 CI 阻断语义。
- 不实现 PR 计数数据库、Dashboard 或自动规则调整。

## 验证

新增 unit/CLI 测试覆盖：新 finding 的输入定位、持久化、按规则统计、未知 finding ID 的失败，以及同一 fingerprint 的覆盖而非重复计数。更新日志模板的敏感信息边界说明。运行完整 `python -m unittest discover -v`、`git diff --check`，并在本地使用临时 findings 文档验证 CLI 的成功与失败路径。
