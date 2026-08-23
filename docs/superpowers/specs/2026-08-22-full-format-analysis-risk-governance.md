# 全格式 analysis、风险排序与产物治理设计

## 目标

把「确定性分析」从仅 JSON/Markdown 透出，扩展到全部五种报告格式，并新增两项能力：

1. **全格式 analysis**：`xlsx` / `docx` / `pdf` 也能渲染每条 finding 的分类、成因、影响、修复建议、参考、`diff_status` 与 `evidence` 摘要。
2. **风险排序**：按**已有确定性信号**（严重度 + 分类 label + diff 状态）对 finding 排序，让审阅者先看到最可处置的条目（confirmed + changed + 高严重度在前）。
3. **产物治理**：报告 CLI 输出一份可校验的 `manifest.json` 清单（文件名 + 字节数 + SHA-256），并固定 CI 产物保留期。

这是「排序」而非「评分」：只使用确定性 label，不引入 baseline 或统计建模。风险*评分*必须等真实 triage 数据就绪后才能做（见 baseline 设计）。

## 设计决策

### 1. 风险排序（`reporting/risk.py`）

```python
LABEL_ORDER = {"confirmed": 0, "suspicious": 1, "possible_false_positive": 2}
DIFF_ORDER  = {"changed": 0, "unknown": 1, "unchanged": 2}

risk_key(finding, analysis_item) -> (
    LABEL_ORDER[label],       # 未分析 -> 3，排最后
    DIFF_ORDER[diff_status],
    SEVERITY_ORDER[severity],
    tool, path, start_line, id,  # 稳定 tiebreak
)
```

排序优先级：**分类 > diff 状态 > 严重度**，之后用 `tool/path/start_line/id` 保证稳定（确定、可复现）。无分析项时退化为严重度排序（与原 `SecurityReport.create` 行为一致）。

- `order_findings(findings, analysis_items_by_id)` 是纯函数，`analysis_items` 为 `{finding_id: AnalysisItem.to_dict()}`。
- 仅在**增强渲染路径**（`--analysis` 传入时）应用；不传 analysis 的普通报告保持严重度排序不变。

### 2. 共享助手（`reporting/render_analysis.py`）

- `analysis_items(analysis) -> dict[id, item_dict]`：把 `AnalysisDocument` 摊平为按 id 索引的 dict。
- `evidence_summary(evidence) -> str`：把 `evidence` 渲染为紧凑可校验字符串 `path:start-end sha256=xxxxxxxx (truncated)`，供五种格式复用，保证展示一致。

### 3. 全格式接线

- `render_excel(report, analysis=None)`：`Findings` 表在既有 10 列后追加 `Classification / Diff Status / Title / Cause / Impact / Remediation / References / Evidence` 8 列（仅当 analysis 传入时）。列宽与页脚打印设置沿用。
- `render_pdf(report, analysis=None)`：每条 finding 在代码/元数据后追加分类与证据段落。
- `render_docx(report, analysis=None)`：`report_dict(report, analysis)` 把 analysis 合并为每条 finding 的 `_analysis` 字段（含预计算 `evidence_summary`），`render_docx.js` 据此追加段落。
- `reporting/cli.py:_render_format`：`json`/`markdown` 在 analysis 传入时走 `render_analysis_*`；`xlsx`/`docx`/`pdf` 直接把 `analysis` 透传给对应渲染器。**所有渲染器在 `analysis=None` 时输出与之前完全一致**（向后兼容）。

### 4. 产物治理（`reporting/manifest.py`）

`render_manifest(entries) -> str` 输出 schema 1.0 的 `manifest.json`：

```json
{
  "schema_version": "1.0",
  "generated_at": "...",
  "artifacts": [
    {"path": "security-report.json", "bytes": 1234, "sha256": "..."}
  ]
}
```

`reporting.cli` 在写出报告组的同时原子写出 `manifest.json`，列入本次生成的每个 `security-report.*`。CI 的 `upload-artifact` 固定 `retention-days: 30` 并把 `manifest.json` 纳入上传清单。`artifacts/` 仍由 `.gitignore` 排除，不提交。

## 流程

```
reporting.cli --analysis analysis.json [--format ...]
  ├─ order_findings(risk_key)  → 风险排序后的 finding 顺序
  ├─ render_excel/docx/pdf/json/markdown  → 五种格式都透出 analysis 字段
  └─ render_manifest  → manifest.json（原子写出，含 SHA-256）
```

## 验收

- `reporting/risk.py`：confirmed/changed/高严重度排前；未分析排最后；无分析退化为严重度排序；tiebreak 稳定。
- 全格式：`xlsx` 追加 8 列分析、`docx`/`pdf` 追加分类/证据段落、`json`/`markdown` 按风险排序透出；`analysis=None` 时各格式输出不变。
- 产物治理：`manifest.json` 与报告组同批原子写出、条目含 `bytes` 与 64 位 `sha256`；CI 上传清单含 `manifest.json` 且 `retention-days: 30`。
- 单测：`python -m unittest tests.test_risk tests.test_manifest tests.test_render_analysis tests.test_reporting_cli tests.test_render_excel tests.test_render_docx tests.test_render_pdf -v`

## 边界（本次不做）

- **风险评分（数值分数）**：需 baseline 与真实误报校准数据，属后续步骤，本次只做确定性排序。
- **baseline 分类（new/existing）与人工处置数据存储**：见 `2026-08-22-baseline-human-triage-design.md`，仅设计、不实现。
- 规则集定制、真实 LLM 调用、合并阻断策略：后置或需单独授权。
