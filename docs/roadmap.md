# 开发路线图

本文描述 CodeSec-Agent 从最小可运行闭环到完整安全审计工作流的阶段规划。

## Phase 1: PR 审查基线

目标：跑通原始 PR-Agent，建立 Pull Request 审查入口。

主要任务：

- 准备 GitHub 测试仓库。
- 添加 PR-Agent GitHub Action。
- 配置模型 API Key。
- 创建测试 Pull Request。
- 验证 PR-Agent 自动生成审查评论。

交付物：

- 可运行的 PR-Agent GitHub Action。
- 一次成功的 PR 审查记录。
- 最小配置说明。

## Phase 2: 静态安全扫描

目标：接入传统安全扫描工具，获得可复现的安全发现。

主要任务：

- 使用 Semgrep 扫描测试仓库。
- 对 Python 项目使用 Bandit。
- 对 Node.js 项目使用 npm audit。
- 将扫描结果保存为 JSON。
- 初步解析扫描器输出。

交付物：

- `semgrep-result.json`
- `bandit-result.json` 或 `npm-audit-result.json`
- 初始扫描结果摘要。

## Phase 3: 结果归一化

目标：将不同扫描器输出转换为统一 finding 数据结构。

主要任务：

- 设计通用 finding 字段。
- 解析 Semgrep 结果。
- 解析 Bandit 结果。
- 解析 npm audit 结果。
- 统一风险等级、文件位置和规则信息。

交付物：

- 扫描结果解析模块。
- 统一 finding 数据结构说明。
- 示例归一化输出。

## Phase 4: Agent 安全分析

目标：将原始扫描结果转换为可读的安全审查结论。

主要任务：

- 设计安全审查 Prompt。
- 将 finding、代码片段和安全参考传入分析流程。
- 生成漏洞解释、影响分析和修复建议。
- 标注确认问题、可疑问题和可能误报。

交付物：

- `prompts/security_review.md`
- 示例 Agent 分析输出。
- 改进版 Markdown 报告。

## Phase 5: 报告生成

目标：形成稳定的审计报告输出能力。

主要任务：

- 生成 Markdown 报告。
- 增加风险汇总。
- 增加发现项明细表。
- 增加修复建议和参考链接。
- 保存完整示例报告。

交付物：

- Markdown 报告生成模块。
- 示例安全审计报告。
- 报告字段说明。

## Phase 6: 自动化与集成

目标：将安全扫描和报告生成接入 CI 或 PR 工作流。

主要任务：

- 添加安全扫描 GitHub Action。
- 保存扫描结果和报告产物。
- 在 PR 评论中输出报告摘要。
- 支持按风险阈值提示或阻断合并。

交付物：

- `.github/workflows/security-scan.yml`
- PR 报告摘要示例。
- 自动化运行说明。

## 后续增强

- 建立 OWASP/CWE 知识库。
- 引入 RAG 检索增强。
- 支持 Word/PDF 报告导出。
- 支持多语言仓库。
- 增加误报过滤和风险评分。
- 构建 Web 可视化界面。
