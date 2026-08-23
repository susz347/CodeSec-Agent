# Phase 4 本地报告设计

## 目标

把一个或多个 schema `1.0` finding JSON 文档汇总为稳定的本地安全报告，首版生成 JSON 和 Markdown；不启动扫描器、不调用模型、不访问 GitHub。

## 架构

`reporting.load_findings` 读取并验证输入；`reporting.models` 定义 `SecurityReport`、扫描来源和严重级别统计；`render_json` 与 `render_markdown` 只消费该报告模型；`reporting.cli` 负责参数和原子写出两个产物。未来 Excel、DOCX、PDF 复用同一模型，不重新解析扫描器输出。

## 输入与输出

- CLI 接受一个或多个 `--input <findings.json>` 与 `--output-dir <目录>`。
- 每份输入必须是对象、`schema_version` 为 `1.0`，并具有 `scan` 对象和 `findings` 数组；否则失败且不写报告。
- 合并保留所有 finding；按 `error`、`warning`、`info`、`unknown` 统计，并稳定排序为严重级别、tool、path、行号、ID。
- 写入被忽略目录的 `security-report.json` 和 `security-report.md`。空 findings 是成功结果。

## Markdown

报告包含标题、生成时间、输入扫描来源、finding 总数、严重级别表，以及按排序顺序的 finding 明细：严重级别、规则、位置、消息、工具、代码（如有）、元数据和原始引用。

## 错误与测试

缺少文件、无效 JSON、不兼容 schema、缺失顶层字段或 finding 非对象都抛出明确错误。离线测试覆盖单/多输入合并、空报告、严重级别统计与排序、JSON/Markdown 确定性输出、无效输入和 CLI 不产生部分产物。最终使用现有三个扫描器产物生成一次真实本地报告。

## 后续边界

Excel、DOCX、PDF 是独立渲染任务；Agent 分析、修复建议、PR 评论和 workflow 不属于本切片。
