# 安全分析 Agent 设计

## 目标

把统一 finding 解释为开发者可执行的安全结论：确认/可疑/误报分类、成因、影响、防御性修复建议和 CWE/OWASP 参考。首版使用确定性规则引擎，LLM 后端留接口，后续授权后接入 DeepSeek。

## 架构

```
统一 finding (schema 1.0)
  -> agent.knowledge.lookup()   本地 CWE/OWASP 子集
  -> agent.security_reviewer    确定性分类 + 组装结论
  -> AnalysisDocument (schema 1.0)
  -> reporting.render_analysis  增强 Markdown/JSON 报告
```

- `agent/models.py`：`AnalysisItem`（finding_id/label/title/cause/impact/remediation/references）与 `AnalysisDocument`。
- `agent/knowledge.py`：`signature()` 把 Semgrep 自由 rule_id、Bandit 不透明 test_id、npm 依赖统一归一化为「概念」字符串；`lookup()` 返回 `RuleKnowledge`，未知规则安全回退。
- `agent/security_reviewer.py`：`ReviewerBackend` Protocol、`DeterministicReviewer`、`LlmReviewer` 桩、模块级 `analyze()`。

## 分类规则（确定性，按序应用）

1. 按严重度打底：error→confirmed，warning→suspicious，info/unknown→possible_false_positive。
2. 测试路径降级（`test*`/`spec` 目录或 `*_test.py`/`test_*.py` 等）→ 降一级。
3. 缺代码片段且非 npm-audit → 降级。
4. 高置信规则（exec/eval/subprocess/sql/命令注入/硬编码凭据/反序列化）且有 code 且非测试路径 → 强制 confirmed。
5. 注释代码（各行均以 `#`/`//`/`/*` 开头）→ possible_false_positive。

## 数据契约

`AnalysisDocument` 输出 `schema_version=1.0`，每个 `AnalysisItem` 必须 `finding_id` 引用输入中存在的 finding `id`，`label` 只能是 `confirmed`/`suspicious`/`possible_false_positive`。

## 边界

- 不读源文件、不调模型、不访问 GitHub；离线确定性、可测。
- 真实 DeepSeek 调用需要单独授权，`LlmReviewer` 当前抛 `NotImplementedError`。
- 分析层不修改代码、不提供利用步骤。

## 验收

- 每条分析项都引用存在的 finding id；label 全部合法；同输入同输出。
- 分类规则边界有单测覆盖（错误/可疑/误报/降级/高置信/注释）。
- 知识库命中与回退有单测覆盖。
- 真实验收使用三个扫描器 fixture 生成分析，人工复核结论合理。
