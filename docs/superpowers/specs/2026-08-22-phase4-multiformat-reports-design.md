# Phase 4 多格式本地报告设计

## 目标

在现有统一 `SecurityReport` 模型之上增加 Excel、DOCX 和 PDF 渲染，使本地报告覆盖 JSON、Markdown、XLSX、DOCX、PDF 五种格式。新切片不重新解析扫描器输出，不调用 DeepSeek，不访问 GitHub，也不改变 Phase 3 扫描器。

## 方案与依赖

- Excel 使用 Python `openpyxl`，直接从报告模型创建工作簿。
- PDF 使用 Python `reportlab`，直接从报告模型创建 A4 报告。
- DOCX 使用 Node.js `docx`，由一个 Python 包装器把报告 JSON 传给独立 JavaScript 渲染器并接收生成的 OOXML 字节。
- Python 依赖写入独立、固定版本的 `requirements-reporting.txt`；Node 依赖由 `package.json` 与 `package-lock.json` 固定。生成报告时不访问网络。

不采用“DOCX 经 LibreOffice 转 PDF”，避免把 LibreOffice 变成运行时强依赖；也不在本切片引入可配置模板系统。

## CLI 与兼容性

`python -m reporting.cli` 保留现有 `--input` 和 `--output-dir`。不传格式参数时仍只生成 JSON 与 Markdown，保证现有命令不因新增依赖而改变行为。

新增可重复的 `--format` 参数，支持 `json`、`markdown`、`xlsx`、`docx`、`pdf` 和 `all`。`--format all` 展开为全部五种格式；重复项去重并保持固定输出顺序。输出文件分别为：

- `security-report.json`
- `security-report.md`
- `security-report.xlsx`
- `security-report.docx`
- `security-report.pdf`

## 渲染结构

Excel 包含三个工作表：

- `Summary`：生成时间、finding 总数和四级严重度统计。
- `Sources`：tool、版本、规则集、目标和扫描开始时间。
- `Findings`：按统一模型顺序写入 ID、严重度、工具、规则、位置、消息、代码、元数据和原始引用。

DOCX 与 PDF 使用相同的信息结构：标题和生成时间、扫描来源表、风险摘要表、按顺序排列的 finding 明细。空结果明确显示 `No findings.`。DOCX 使用显式 A4 页面尺寸、专业字体、固定表格宽度和页脚页码。PDF 使用可配置的 `CODESEC_REPORT_FONT` 字体路径，未配置时依次查找 Windows Microsoft YaHei、Linux Noto Sans CJK 和 DejaVu Sans；如果没有可用字体则返回明确错误。

## 数据流与事务写入

所有渲染器只接收 `SecurityReport`，返回文件字节，不自行读取 finding 文档或决定输出路径。CLI 先完成所有选定格式的渲染，再把每种格式写入输出目录中的同级临时文件。

提交阶段把已有目标文件移动到独立备份，再按固定顺序替换全部新文件。任一替换失败时删除本轮已经提交的新文件，并恢复所有旧文件；成功后删除备份。临时文件与备份文件都使用固定、仅限报告文件名的路径，不接受输入内容控制文件名。

## 错误处理

- 缺少 Python 或 Node 报告依赖时，CLI 返回非零退出码并指出安装命令。
- DOCX 子进程失败、PDF 字体不可用或任一渲染器异常时，不更新任何选定报告。
- 无效 finding 输入沿用现有 `ReportInputError`；空 findings 仍是成功结果。
- 不把报告正文写入错误日志，避免扫描证据或源代码片段意外泄露到终端日志。

## 测试与验收

测试保持针对性，避免为排版细节建立脆弱快照：

- Excel：加载工作簿并验证三个工作表、摘要数值、表头和一条 finding。
- DOCX：解包 OOXML 并验证文档有效、标题、摘要和 finding 内容存在。
- PDF：解析页数与提取文本，验证标题、摘要和 finding 内容存在。
- CLI：验证默认格式不变、`--format all` 生成五个文件，以及多格式提交失败时恢复旧文件组。
- 真实验收：使用现有 Semgrep、Bandit、npm audit 三份 schema 1.0 产物生成五种报告；解析每个文件，并对 XLSX、DOCX、PDF 做一次渲染或视觉抽查。

## 后续边界

本切片结束后，Phase 4 仍保留 Agent 漏洞解释、误报分类、修复建议、CWE/OWASP 增强、GitHub Action、PR 摘要和风险阈值策略。这些任务不与多格式渲染器耦合。
