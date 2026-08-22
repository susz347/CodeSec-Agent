# 上下文证据与 PR diff 过滤设计

## 目标

让确定性分析 Agent 的输出从「仅凭严重度 + 规则知识打标签」升级为**带证据、可验证**的结论，为后续 gated LLM 与 baseline 校准打好输入基础。本切片交付两个能力：

1. **上下文证据（#2）**：安全读取 finding 周围的局部代码上下文，带安全路径约束与行数/字节预算，产出结构化 `ContextEvidence`。
2. **diff 过滤（#6 第一步）**：解析 PR/git diff，把每条 finding 标注为 `changed` / `unchanged` / `unknown`。

两者都固化为**机器可验证的数据字段**（`analysis.json` 中每条 item 的 `diff_status` 与 `evidence`），而不是模型写在 `cause` 文本里的自我声明。

## 安全边界

- 上下文读取是本项目分析层**唯一**读取源文件的地方。它只在显式传入 `--repo-root` 时启用，默认不读源文件。
- 路径约束：finding `path` 必须是相对路径（拒绝绝对路径、Windows 盘符、UNC、`..` 组件）；`(repo_root / path).resolve()` 必须落在 `repo_root` 之内（同时拦截符号链接逃逸）；必须是普通文件。
- 违规抛 `PathEscapeError`，调用方只跳过该条证据、**永不读取根外文件**。
- 预算：默认窗口 `lines_before=10 / lines_after=10`，`snippet` 上限 `max_bytes=8192`，超出截断并置 `truncated=True`；`sha256` 取最终返回的 snippet 文本（机器可验「展示即所读」）。

## 数据模型

`AnalysisItem` 新增两个向后兼容字段：

- `diff_status`: `changed` / `unchanged` / `unknown`（默认 `unknown`，未传 diff 时一律 unknown，不与 unchanged 混淆）。
- `evidence`: 可选 `dict`，为 `ContextEvidence.to_dict()`（未传 repo-root 或读取失败时为 `None`）。

旧 `analysis.json`（无这两个字段）仍可 `from_dict` 解析。

## 流程

```
scanner 产物 (findings.json)
  → agent.cli [--diff pr.diff] [--repo-root .]
      ├─ parse_unified_diff → classify_finding → diff_statuses
      └─ read_context → ContextEvidence → evidence
  → analyze(document, diff_statuses, evidence) → analysis.json/.md
  → reporting.cli --analysis → 增强报告透出 diff_status + evidence 摘要
  → reporting.summary → PR 摘要透出 changed/unchanged/unknown 计数
```

## 验收

- `agent/context.py`：根内读取返回正确窗口/端点/sha256；`..`、绝对路径、符号链接逃逸抛 `PathEscapeError`；缺失文件抛 `ContextError`；超预算截断。
- `agent/diff.py`：单 hunk/多文件/新文件解析；changed（重叠）、unchanged（同文件不重叠）、unknown（路径不在 diff）。
- 分析/报告/摘要：新字段正确透出，旧文档仍可解析。
- 单测：`python -m unittest tests.test_context tests.test_diff tests.test_agent_models tests.test_security_reviewer tests.test_render_analysis tests.test_summary -v`

## 边界（本次不做）

- **baseline 分类（new/existing）**：需基线数据与真值，属 #6 第二步，本次只 diff 过滤出 changed/unchanged。
- 真实 LLM 调用 / gated LLM / LLM 契约 mock：属 7 步计划第 4/6 步。
- 测试 CI workflow、风险排序、规则集定制、产物治理：后置。
