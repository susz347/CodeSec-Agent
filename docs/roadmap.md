# 开发路线图

本文描述 CodeSec-Agent 从 PR-Agent 最小闭环到完整安全审计工作流的四个阶段。阶段名称与 README、部署指南和新手指南保持一致。

## Phase 1: GitHub Actions PR-Agent

目标：在 GitHub Actions 中跑通自动 PR review，并建立可信默认分支配置。

主要任务：

- 添加固定 SHA 的 PR-Agent workflow。
- 配置 DeepSeek Repository Secret。
- 只处理同仓库、非 Bot PR，并使用最小权限。
- 从更新后的 `main` 创建短生命周期验证 PR。
- 验证首次 review 与 synchronize 更新行为。

交付物：

- 可运行的 PR-Agent GitHub Action。
- 一次成功的 Action review 记录。
- 无凭据泄露的日志与最小权限说明。

## Phase 2: 本地 PR-Agent CLI

目标：在 Windows 本地使用与 GitHub Actions 相同的可信配置，对同一个短生命周期验证 PR 执行 review。

主要任务：

- 使用 Python 3.12 虚拟环境安装固定版本的本地 CLI。
- 创建仅限目标仓库和必要权限的短期 Fine-grained PAT。
- 只在用户自己的 PowerShell 进程中注入临时凭据。
- 显式读取默认分支 `main` 中已审核的共享配置。
- 验证评论后清理凭据、验证 PR、分支和临时探针。

交付物：

- 一次成功的本地 CLI review 记录。
- 最小权限与凭据清理记录。
- 不含临时探针垃圾的干净仓库状态。

## Phase 3: 静态安全扫描与结果归一化

目标：先用 Semgrep 获得可复现的安全发现，并转换为统一 finding 数据结构；在此切片完成真实验证后，再独立接入其他扫描器。

主要任务：

- 使用固定版本 Semgrep 和显式 `p/security-audit` 规则集扫描目标目录。
- 保存原始 Semgrep JSON，并归一化为版本化 finding 文档。
- 统一风险等级、文件位置、规则 ID 和证据信息。
- 在 Semgrep 真实验证完成后，分别以独立适配器接入 Bandit 与 npm audit。

交付物：

- Semgrep 的原始与归一化 JSON 结果。
- Semgrep 扫描执行器与解析模块。
- 统一 finding 数据结构说明与示例输出。

当前状态：Semgrep、Bandit 和 npm audit 已完成本地验证与统一归一化。Phase 3 不调用 DeepSeek、不写 PR 评论、不阻断合并；`artifacts/` 中的本地扫描产物不提交到 Git。

## Phase 4: Agent 分析、报告与自动化

目标：把统一 finding 和代码上下文转换为可读的安全结论、稳定报告，并接入自动化工作流。

主要任务：

- 设计和迭代安全审查 Prompt。
- 结合 finding、代码片段和安全参考生成漏洞解释。
- 标注确认问题、可疑问题和可能误报。
- 合并多个 schema 1.0 finding 文档，生成 JSON/Markdown 报告、风险汇总和发现项明细。
- 在统一报告模型稳定后，依次增加 Excel、DOCX 和 PDF 渲染器。
- 加入修复建议、CWE/OWASP 参考和完整示例报告。
- 添加安全扫描 GitHub Action，保存扫描结果与报告产物。
- 在 PR 评论中输出摘要，并探索按风险阈值提示或阻断合并。

交付物：

- 安全分析输出与改进后的 Prompt。
- JSON/Markdown 报告生成模块、示例报告和字段说明。
- Excel、DOCX 和 PDF 报告导出模块。
- `.github/workflows/security-scan.yml` 与 PR 报告摘要示例。
- 自动化运行说明。

当前状态：本地报告切片已完成统一报告模型、严格输入校验、多扫描器合并、稳定排序、JSON、Markdown、Excel、DOCX、PDF 渲染，以及任意选中报告组的写入回滚。真实三扫描器产物已经完成结构与视觉验证。报告流程不调用 DeepSeek、不访问 GitHub，也不提交 `artifacts/`；Agent 分析、示例报告、GitHub 自动化和风险阈值策略仍待后续切片实现。

## 后续增强

- 建立 OWASP/CWE 知识库。
- 引入 RAG 检索增强。
- 支持多语言仓库。
- 增加误报过滤和风险评分。
- 构建 Web 可视化界面。
